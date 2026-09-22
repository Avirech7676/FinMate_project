"""
FinMate 2.0 Machine Learning Evaluation Test Suite (Phase 5)
Evaluates:
1. Layered Anomaly Detection against a labeled ground-truth synthetic dataset:
   - Precision, Recall, F1 Score, False Positives, False Negatives.
2. Spending Forecasting against a Simple Moving Average (SMA) baseline:
   - Evaluated across 7-day, 30-day, and 90-day horizons.
   - Metrics: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Mean Absolute Percentage Error (MAPE).
"""

import math
import numpy as np
import pytest
from datetime import datetime, timedelta
from typing import List

import models
from app.analytics.anomalies import LayeredAnomalyDetector
from app.analytics.forecasting import SpendingForecaster


class TestAnomalyDetectionEvaluation:
    """
    Evaluates 3-tier anomaly detection on a reproducible labeled benchmark.
    """

    @pytest.fixture
    def labeled_anomaly_dataset(self) -> tuple[List[models.Transaction], set[int]]:
        """
        Generates 120 synthetic transactions spanning 90 days with 5 labeled anomalies:
        - Tx 101: 3x Category median spike on groceries ($450 vs $35)
        - Tx 102: Extreme luxury/electronics spike ($850 vs $40)
        - Tx 103: Statistically high restaurant spend ($380, Z > 3.0)
        - Tx 104: High utility spike ($420 vs $60)
        - Tx 105: Weekend multidimensional outlier ($520)
        """
        np.random.seed(42)
        transactions = []
        base_date = datetime(2026, 1, 1)

        # 1. 115 Regular normal transactions across categories
        categories = {
            "groceries": (35.0, 8.0),
            "dining": (28.0, 7.0),
            "utilities": (65.0, 10.0),
            "transport": (22.0, 5.0),
            "entertainment": (40.0, 12.0)
        }

        tx_id = 1
        for day in range(90):
            dt = base_date + timedelta(days=day)
            # 1 to 2 transactions per day
            for cat, (mean_amt, std_amt) in categories.items():
                if np.random.rand() > 0.72:
                    amt = max(5.0, round(float(np.random.normal(mean_amt, std_amt)), 2))
                    transactions.append(models.Transaction(
                        transaction_id=tx_id,
                        user_id=1,
                        amount=amt,
                        category=cat,
                        date=dt,
                        description=f"Normal {cat} purchase #{tx_id}",
                        source="manual"
                    ))
                    tx_id += 1

        # 2. Inject 5 specific ground-truth anomalies
        ground_truth_anomaly_ids = {1001, 1002, 1003, 1004, 1005}

        # Anomaly 1: Groceries spike ($450.0)
        transactions.append(models.Transaction(
            transaction_id=1001,
            user_id=1,
            amount=450.0,
            category="groceries",
            date=base_date + timedelta(days=20),
            description="Abnormal massive bulk groceries purchase",
            source="manual"
        ))

        # Anomaly 2: Extreme luxury spike ($850.0)
        transactions.append(models.Transaction(
            transaction_id=1002,
            user_id=1,
            amount=850.0,
            category="dining",
            date=base_date + timedelta(days=40),
            description="Fine dining gala dinner",
            source="manual"
        ))

        # Anomaly 3: High utility spike ($420.0)
        transactions.append(models.Transaction(
            transaction_id=1003,
            user_id=1,
            amount=420.0,
            category="utilities",
            date=base_date + timedelta(days=55),
            description="Unusual triple utility adjustment",
            source="manual"
        ))

        # Anomaly 4: Restaurant statistical outlier ($380.0)
        transactions.append(models.Transaction(
            transaction_id=1004,
            user_id=1,
            amount=380.0,
            category="dining",
            date=base_date + timedelta(days=70),
            description="Large party dining bill",
            source="manual"
        ))

        # Anomaly 5: Weekend multidimensional outlier ($520.0)
        transactions.append(models.Transaction(
            transaction_id=1005,
            user_id=1,
            amount=520.0,
            category="entertainment",
            date=base_date + timedelta(days=82),
            description="VIP concert pass",
            source="manual"
        ))

        return transactions, ground_truth_anomaly_ids

    def test_evaluate_anomaly_detection_performance(self, labeled_anomaly_dataset):
        transactions, ground_truth_ids = labeled_anomaly_dataset

        # Run Layered Anomaly Detection
        detected_anomalies = LayeredAnomalyDetector.detect_anomalies(
            transactions,
            monthly_income=4500.0
        )
        detected_ids = {a.transaction_id for a in detected_anomalies}

        true_positives = len(detected_ids.intersection(ground_truth_ids))
        false_positives = len(detected_ids - ground_truth_ids)
        false_negatives = len(ground_truth_ids - detected_ids)
        total_normal = len(transactions) - len(ground_truth_ids)
        true_negatives = total_normal - false_positives

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / len(ground_truth_ids)
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        print("\n--- ANOMALY DETECTION EVALUATION RESULTS ---")
        print(f"Total Transactions: {len(transactions)}")
        print(f"Ground Truth Anomalies: {len(ground_truth_ids)}")
        print(f"Detected Anomalies: {len(detected_ids)}")
        print(f"True Positives: {true_positives}")
        print(f"False Positives: {false_positives}")
        print(f"False Negatives: {false_negatives}")
        print(f"Precision: {precision:.4f} ({precision*100:.2f}%)")
        print(f"Recall:    {recall:.4f} ({recall*100:.2f}%)")
        print(f"F1 Score:  {f1:.4f}")

        # Assert minimum acceptable production standards
        assert recall >= 0.80, f"Recall too low: {recall}"
        assert precision >= 0.70, f"Precision too low: {precision}"
        assert f1 >= 0.75, f"F1 score too low: {f1}"


class TestForecastingEvaluation:
    """
    Evaluates Holt-Winters exponential smoothing forecaster vs Simple Moving Average (SMA) baseline
    across 7-day, 30-day, and 90-day prediction horizons.
    """

    @pytest.fixture
    def synthetic_timeseries_dataset(self):
        """
        Generates 180 days of spending data:
        - 90 days train history
        - 90 days actual ground truth future
        Generates underlying daily spend with weekly seasonality and mild upward trend.
        """
        np.random.seed(123)
        start_date = datetime(2026, 1, 1)

        train_txns = []
        future_daily_spend = []

        tx_id = 1
        for day in range(180):
            current_date = start_date + timedelta(days=day)
            dow = current_date.weekday()
            # Base spend $50 + weekend boost $25 on Fri/Sat (dow 4, 5) + mild trend + noise
            seasonality = 25.0 if dow in (4, 5) else 0.0
            trend = 0.08 * day
            noise = float(np.random.normal(0, 6.0))
            daily_amount = max(15.0, round(50.0 + seasonality + trend + noise, 2))

            if day < 90:
                # Historical train data
                train_txns.append(models.Transaction(
                    transaction_id=tx_id,
                    user_id=1,
                    amount=daily_amount,
                    category="groceries" if dow % 2 == 0 else "dining",
                    date=current_date,
                    description=f"Day {day} daily purchase",
                    source="manual"
                ))
                tx_id += 1
            else:
                # Future test data for validation
                future_daily_spend.append(daily_amount)

        return train_txns, future_daily_spend

    def test_evaluate_forecasting_vs_baseline(self, synthetic_timeseries_dataset):
        train_txns, future_daily_spend = synthetic_timeseries_dataset

        # 1. Generate FinMate forecast
        forecast = SpendingForecaster.generate_forecast(train_txns, monthly_income=3500.0)
        hw_pred_7 = forecast["forecast_7_day"]["projected_spending"]
        hw_pred_30 = forecast["forecast_30_day"]["projected_spending"]
        hw_pred_90 = forecast["forecast_90_day"]["projected_spending"]

        # 2. Simple Baseline (Simple 14-day Moving Average)
        recent_14 = [float(t.amount) for t in train_txns[-14:]]
        sma_daily_rate = float(np.mean(recent_14))
        sma_pred_7 = round(sma_daily_rate * 7, 2)
        sma_pred_30 = round(sma_daily_rate * 30, 2)
        sma_pred_90 = round(sma_daily_rate * 90, 2)

        # 3. Ground Truth Totals
        actual_7 = sum(future_daily_spend[:7])
        actual_30 = sum(future_daily_spend[:30])
        actual_90 = sum(future_daily_spend[:90])

        horizons = [
            ("7-Day", 7, actual_7, hw_pred_7, sma_pred_7),
            ("30-Day", 30, actual_30, hw_pred_30, sma_pred_30),
            ("90-Day", 90, actual_90, hw_pred_90, sma_pred_90)
        ]

        print("\n--- FORECASTING EVALUATION RESULTS ---")
        print(f"{'Horizon':<8} | {'Actual ($)':<10} | {'FinMate HW ($)':<14} | {'Baseline ($)':<12} | {'HW Error':<10} | {'Base Error':<10}")
        print("-" * 75)

        for name, days, actual, hw_pred, base_pred in horizons:
            hw_err = abs(actual - hw_pred)
            base_err = abs(actual - base_pred)
            hw_pct = (hw_err / actual) * 100
            base_pct = (base_err / actual) * 100

            print(f"{name:<8} | {actual:<10.2f} | {hw_pred:<14.2f} | {base_pred:<12.2f} | {hw_err:<10.2f} ({hw_pct:.1f}%) | {base_err:<10.2f} ({base_pct:.1f}%)")

            # Assert forecasting error remains within bounds (< 15% MAPE for 7d & 30d)
            assert hw_pct < 15.0, f"FinMate error too high for {name}: {hw_pct:.2f}%"

        # Point-by-point daily metrics across 30-day horizon
        daily_actuals = future_daily_spend[:30]
        daily_hw_rates = [hw_pred_30 / 30.0] * 30
        daily_base_rates = [sma_pred_30 / 30.0] * 30

        hw_mae = float(np.mean([abs(a - p) for a, p in zip(daily_actuals, daily_hw_rates)]))
        hw_rmse = float(np.sqrt(np.mean([(a - p) ** 2 for a, p in zip(daily_actuals, daily_hw_rates)])))
        hw_mape = float(np.mean([abs(a - p) / a for a, p in zip(daily_actuals, daily_hw_rates)])) * 100

        base_mae = float(np.mean([abs(a - p) for a, p in zip(daily_actuals, daily_base_rates)]))
        base_rmse = float(np.sqrt(np.mean([(a - p) ** 2 for a, p in zip(daily_actuals, daily_base_rates)])))
        base_mape = float(np.mean([abs(a - p) / a for a, p in zip(daily_actuals, daily_base_rates)])) * 100

        print("\n--- 30-DAY DAILY POINTWISE METRICS ---")
        print(f"FinMate Model -> MAE: ${hw_mae:.2f}, RMSE: ${hw_rmse:.2f}, MAPE: {hw_mape:.2f}%")
        print(f"SMA Baseline  -> MAE: ${base_mae:.2f}, RMSE: ${base_rmse:.2f}, MAPE: {base_mape:.2f}%")

        assert hw_mae < 25.0
        assert hw_rmse < 30.0
