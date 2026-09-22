import pytest
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import models
from app.analytics.subscriptions import SubscriptionIntelligenceEngine
from app.analytics.cashflow import CashFlowEngine

def test_subscription_detection():
    # 3 recurring monthly Netflix charges ~30 days apart
    base_date = datetime(2026, 6, 15)
    txns = [
        models.Transaction(transaction_id=1, amount=15.99, category="entertainment", description="Netflix.com", date=base_date),
        models.Transaction(transaction_id=2, amount=15.99, category="entertainment", description="Netflix.com", date=base_date + timedelta(days=30)),
        models.Transaction(transaction_id=3, amount=15.99, category="entertainment", description="Netflix.com", date=base_date + timedelta(days=61)),
    ]

    subs = SubscriptionIntelligenceEngine.detect_subscriptions(txns, user_id=42)
    assert len(subs) == 1
    netflix = subs[0]
    assert netflix.frequency == "monthly"
    assert netflix.amount == 15.99
    assert netflix.occurrences == 3
    assert netflix.confidence >= 0.7
    assert netflix.annualized_cost == round(15.99 * 12, 2)

def test_cashflow_engine_projection():
    user = models.User(user_id=42, email="cashflow@test.com")
    now = datetime.utcnow()
    txns = [
        models.Transaction(transaction_id=1, amount=1200.0, category="housing", description="Apartment Rent", date=now - timedelta(days=5)),
        models.Transaction(transaction_id=2, amount=300.0, category="food", description="Groceries", date=now - timedelta(days=10)),
        models.Transaction(transaction_id=3, amount=15.0, category="entertainment", description="Spotify", date=now - timedelta(days=15)),
        models.Transaction(transaction_id=4, amount=15.0, category="entertainment", description="Spotify", date=now - timedelta(days=45)),
    ]
    goals = [
        models.BudgetGoal(
            goal_id=1,
            user_id=42,
            goal_type="vacation",
            target_amount=1200.0,
            current_progress=600.0,
            deadline=now + timedelta(days=60),
            status="active"
        )
    ]

    res = CashFlowEngine.calculate_cashflow(
        user=user,
        monthly_income=3500.0,
        transactions=txns,
        goals=goals,
        initial_balance=5000.0,
        days_forward=30
    )

    assert res["monthly_income"] == 3500.0
    assert res["current_monthly_expenses"]["fixed"] == 1200.0
    assert res["current_cash_flow"] > 0
    assert res["cash_flow_risk"] in ["low", "moderate"]
    assert len(res["balance_projection_30d"]) == 30
    # Day 30 balance should have positive projection
    assert res["balance_projection_30d"][-1]["projected_balance"] > 5000.0
