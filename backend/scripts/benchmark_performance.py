"""
FinMate 2.0 Performance & Scalability Benchmark (Phase 7)
Benchmarks database query execution, transaction retrieval, analytics,
anomaly detection, forecasting, health scoring, and cash-flow projection
at 10,000 and 100,000 synthetic transaction scales.
Records exact p50 latency, p95 latency, and error rates.
"""

import os
import sys
import time
import json
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base
import models
from app.repositories.transaction_repo import TransactionRepository
from app.analytics.spending import SpendingAnalytics
from app.analytics.anomalies import LayeredAnomalyDetector
from app.analytics.forecasting import SpendingForecaster
from app.analytics.health_score import ExplainableHealthScoreEngine
from app.analytics.cashflow import CashFlowEngine

BENCH_DB_URL = "sqlite:///./benchmark_perf.db"


def run_benchmark():
    if os.path.exists("benchmark_perf.db"):
        try:
            os.remove("benchmark_perf.db")
        except Exception:
            pass

    engine = create_engine(BENCH_DB_URL, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = Session()

    # Create benchmark user
    bench_user = models.User(
        email="bench_user@finmate.local",
        password_hash="bench_hash",
        full_name="Benchmark User",
        currency="USD",
        currency_symbol="$",
        preferences=json.dumps({"monthly_budget": 3000.0})
    )
    session.add(bench_user)
    session.commit()
    session.refresh(bench_user)

    user_id = bench_user.user_id

    # Create goals
    g1 = models.BudgetGoal(
        user_id=user_id,
        goal_type="savings",
        target_amount=5000.0,
        current_progress=1200.0,
        deadline=datetime.utcnow() + timedelta(days=90),
        status="active"
    )
    session.add(g1)
    session.commit()

    scales = [10_000, 100_000]
    final_report = {}

    for target_count in scales:
        print(f"\n=======================================================")
        print(f"BENCHMARKING SCALE: {target_count:,} TRANSACTIONS")
        print(f"=======================================================")

        # Count current transactions
        current_count = session.query(models.Transaction).filter_by(user_id=user_id).count()
        needed = target_count - current_count

        if needed > 0:
            print(f"Generating and bulk inserting {needed:,} synthetic transactions...")
            t0 = time.perf_counter()
            categories = ["groceries", "dining", "utilities", "transport", "entertainment", "shopping", "health"]
            batch_size = 5000
            now = datetime.utcnow()

            batches = []
            for i in range(needed):
                days_ago = int(i % 365)
                dt = now - timedelta(days=days_ago, minutes=int(i % 1440))
                amt = round(float(10.0 + (i % 150) + np.random.uniform(0.5, 5.0)), 2)
                cat = categories[i % len(categories)]
                batches.append({
                    "user_id": user_id,
                    "amount": amt,
                    "category": cat,
                    "date": dt,
                    "description": f"Benchmark synthetic txn #{current_count + i + 1}",
                    "source": "bench"
                })

                if len(batches) >= batch_size:
                    session.bulk_insert_mappings(models.Transaction, batches)
                    session.commit()
                    batches = []

            if batches:
                session.bulk_insert_mappings(models.Transaction, batches)
                session.commit()

            print(f"Bulk insert completed in {time.perf_counter() - t0:.2f}s.")

        txn_repo = TransactionRepository(session)
        now = datetime.utcnow()
        start_30d = now - timedelta(days=30)
        start_90d = now - timedelta(days=90)
        start_180d = now - timedelta(days=180)

        # Benchmark tasks with explicit workload definitions
        tasks = {
            "Transaction Retrieval (50 limit)": {
                "fn": lambda: txn_repo.list_by_user(user_id=user_id, limit=50, offset=0),
                "operation": "Single-user indexed pagination query",
                "workload_size": "50 transactions"
            },
            "Transaction Retrieval (200 limit)": {
                "fn": lambda: txn_repo.list_by_user(user_id=user_id, limit=200, offset=0),
                "operation": "Single-user indexed pagination query",
                "workload_size": "200 transactions"
            },
            "Analytics (30-day range aggregate)": {
                "fn": lambda: SpendingAnalytics.compute_spending_summary(
                    txn_repo.get_in_date_range(user_id, start_30d, now)
                ),
                "operation": "Date range query + categorical spending aggregation",
                "workload_size": "All transactions in 30-day window (~82-820 txns)"
            },
            "Anomaly Detection (90-day window capped)": {
                "fn": lambda: LayeredAnomalyDetector.detect_anomalies(
                    txn_repo.get_in_date_range(user_id, start_90d, now)[:300],
                    monthly_income=4000.0
                ),
                "operation": "3-tier Rule + Statistical + Isolation Forest anomaly detection",
                "workload_size": "300 transactions (capped slice)"
            },
            "Forecast Generation (180-day window capped)": {
                "fn": lambda: SpendingForecaster.generate_forecast(
                    txn_repo.get_in_date_range(user_id, start_180d, now)[:500],
                    monthly_income=4000.0
                ),
                "operation": "Statsmodels Holt-Winters triple exponential smoothing",
                "workload_size": "500 transactions (capped slice)"
            },
            "Explainable Health Score": {
                "fn": lambda: ExplainableHealthScoreEngine.calculate(
                    monthly_income=4000.0,
                    monthly_spending=2450.0,
                    monthly_budget=3000.0,
                    daily_spending_history=[75.0, 80.0, 95.0, 60.0, 110.0, 50.0, 85.0],
                    goal_statuses=["on_track"]
                ),
                "operation": "Multi-factor explainable health score calculation",
                "workload_size": "7 daily points + goal status vector"
            },
            "Cash-Flow Projection (30 days forward)": {
                "fn": lambda: CashFlowEngine.calculate_cashflow(
                    user=bench_user,
                    monthly_income=4000.0,
                    transactions=txn_repo.get_in_date_range(user_id, start_30d, now)[:200],
                    goals=[g1],
                    initial_balance=3500.0,
                    days_forward=30
                ),
                "operation": "30-day daily balance trajectory & recurring subscription projection",
                "workload_size": "200 transactions (capped slice) + 1 goal"
            }
        }

        scale_results = {}
        iterations = 25

        for name, task_info in tasks.items():
            durations = []
            errors = 0
            fn = task_info["fn"]
            for _ in range(iterations):
                start = time.perf_counter()
                try:
                    fn()
                    durations.append((time.perf_counter() - start) * 1000.0)  # ms
                except Exception as e:
                    errors += 1

            p50 = float(np.percentile(durations, 50)) if durations else 0.0
            p95 = float(np.percentile(durations, 95)) if durations else 0.0
            error_rate = (errors / iterations) * 100.0

            scale_results[name] = {
                "dataset_size": target_count,
                "workload_size": task_info["workload_size"],
                "operation": task_info["operation"],
                "p50_ms": round(p50, 2),
                "p95_ms": round(p95, 2),
                "error_rate_pct": round(error_rate, 1)
            }
            print(f"-> {name:<44} [Workload: {task_info['workload_size']:<32}] | p50: {p50:>6.2f} ms | p95: {p95:>6.2f} ms | Err: {error_rate:.1f}%")

        final_report[f"{target_count:,}"] = scale_results

    session.close()
    engine.dispose()
    if os.path.exists("benchmark_perf.db"):
        try:
            os.remove("benchmark_perf.db")
        except Exception:
            pass

    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "benchmark_results.json")
    with open(output_path, "w") as f:
        json.dump(final_report, f, indent=2)

    print("\nBenchmark successfully completed. Results saved to benchmark_results.json.")
    return final_report


if __name__ == "__main__":
    run_benchmark()
