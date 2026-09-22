import pytest
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base
import models
import schemas
from app.services.user_service import UserService
from app.analytics.spending import SpendingAnalytics
from app.analytics.rules import FinancialRuleEngine

TEST_DB_URL = "sqlite:///./test_analytics.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    try:
        if os.path.exists("test_analytics.db"):
            os.remove("test_analytics.db")
    except Exception:
        pass

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_spending_analytics_calculations():
    now = datetime.utcnow()
    txns = [
        models.Transaction(transaction_id=1, amount=100.0, category="food", description="Starbucks", date=now),
        models.Transaction(transaction_id=2, amount=50.0, category="food", description="Starbucks", date=now),
        models.Transaction(transaction_id=3, amount=200.0, category="shopping", description="Amazon", date=now),
    ]

    summary = SpendingAnalytics.compute_spending_summary(txns)
    assert summary["total_spent"] == 350.0
    assert summary["transaction_count"] == 3
    assert summary["average_transaction"] == round(350.0 / 3, 2)
    assert summary["category_breakdown"]["food"] == 150.0
    assert summary["category_breakdown"]["shopping"] == 200.0
    assert summary["highest_transaction"]["amount"] == 200.0

def test_monthly_comparison_calculation():
    now = datetime.utcnow()
    curr_txns = [
        models.Transaction(transaction_id=1, amount=300.0, category="food", description="Groceries", date=now),
    ]
    prior_txns = [
        models.Transaction(transaction_id=2, amount=200.0, category="food", description="Groceries", date=now),
    ]

    comp = SpendingAnalytics.compute_monthly_comparison(curr_txns, prior_txns)
    assert comp["current_month_total"] == 300.0
    assert comp["prior_month_total"] == 200.0
    assert comp["net_difference"] == 100.0
    assert comp["percentage_change"] == 50.0

def test_financial_rule_engine(db_session):
    user = models.User(user_id=1, email="rules@test.com", currency="USD")
    goals = [
        models.BudgetGoal(
            goal_id=10,
            user_id=1,
            goal_type="emergency_fund",
            target_amount=1000.0,
            current_progress=100.0,
            deadline=datetime.utcnow() + timedelta(days=5),
            status="active"
        )
    ]
    txns = [
        models.Transaction(transaction_id=99, user_id=1, amount=650.0, category="electronics", description="Laptop Monitor", date=datetime.utcnow())
    ]

    # Evaluate with spending (2500) > income (2000)
    signals = FinancialRuleEngine.evaluate_all(
        user=user,
        current_month_spending=2500.0,
        monthly_income=2000.0,
        goals=goals,
        recent_transactions=txns
    )

    rule_ids = [s.rule_id for s in signals]
    assert "RULE_CASHFLOW_DEFICIT" in rule_ids
    assert "RULE_GOAL_AT_RISK_10" in rule_ids
    assert "RULE_HIGH_EXPENSE_99" in rule_ids
