"""
FinMate 2.0 Cross-User Security Regression Tests (Phase 2)
Verifies strict data isolation between User A and User B across:
- Transactions (CRUD & list)
- Goals (CRUD & pacing)
- Analytics & Financial Overview
- Spending Forecasts
- Explainable Health Scores
- Purchase Simulations
- AI Chat Context & Tool Execution
- Summary & Downloadable HTML Reports
- Data Export & Account Deletion Isolation
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from database import Base
import models
import auth

TEST_DB_URL = "sqlite:///./test_cross_user_security.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_cross_user_db():
    app.dependency_overrides[get_db] = override_get_db
    yield

@pytest.fixture(scope="module", autouse=True)
def setup_cross_user_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Seed User A
    db = TestingSessionLocal()
    user_a = models.User(
        email="usera@example.com",
        password_hash=auth.get_password_hash("PasswordA123!"),
        full_name="User Alpha",
        currency="USD",
        currency_symbol="$",
        preferences=json.dumps({"monthly_budget": 2000.0})
    )
    db.add(user_a)
    db.commit()
    db.refresh(user_a)

    prof_a = models.FinancialProfile(
        user_id=user_a.user_id,
        monthly_income=4000.0,
        employment_type="full-time",
        risk_tolerance="moderate"
    )
    db.add(prof_a)

    # User A transactions
    t_a = models.Transaction(
        user_id=user_a.user_id,
        amount=55.0,
        category="groceries",
        description="Alpha Supermarket Spend",
        date=datetime.utcnow() - timedelta(days=2),
        source="manual"
    )
    db.add(t_a)

    # User A goal
    g_a = models.BudgetGoal(
        user_id=user_a.user_id,
        goal_type="savings",
        target_amount=1000.0,
        current_progress=200.0,
        deadline=datetime.utcnow() + timedelta(days=60),
        status="active"
    )
    db.add(g_a)

    # Seed User B
    user_b = models.User(
        email="userb@example.com",
        password_hash=auth.get_password_hash("PasswordB123!"),
        full_name="User Beta",
        currency="EUR",
        currency_symbol="€",
        preferences=json.dumps({"monthly_budget": 5000.0})
    )
    db.add(user_b)
    db.commit()
    db.refresh(user_b)

    prof_b = models.FinancialProfile(
        user_id=user_b.user_id,
        monthly_income=8000.0,
        employment_type="contractor",
        risk_tolerance="aggressive"
    )
    db.add(prof_b)

    # User B transactions
    t_b = models.Transaction(
        user_id=user_b.user_id,
        amount=999.0,
        category="luxury",
        description="Beta Confidential Diamond Purchase",
        date=datetime.utcnow() - timedelta(days=1),
        source="manual"
    )
    db.add(t_b)

    # User B goal
    g_b = models.BudgetGoal(
        user_id=user_b.user_id,
        goal_type="investment",
        target_amount=50000.0,
        current_progress=10000.0,
        deadline=datetime.utcnow() + timedelta(days=120),
        status="active"
    )
    db.add(g_b)
    db.commit()

    db.close()

    yield

    engine.dispose()
    import os
    if os.path.exists("test_cross_user_security.db"):
        try:
            os.remove("test_cross_user_security.db")
        except Exception:
            pass


@pytest.fixture(scope="module")
def tokens():
    app.dependency_overrides[get_db] = override_get_db
    # Login User A
    res_a = client.post("/login", data={"username": "usera@example.com", "password": "PasswordA123!"})
    token_a = res_a.json()["access_token"]

    # Login User B
    res_b = client.post("/login", data={"username": "userb@example.com", "password": "PasswordB123!"})
    token_b = res_b.json()["access_token"]

    db = TestingSessionLocal()
    user_a = db.query(models.User).filter_by(email="usera@example.com").first()
    user_b = db.query(models.User).filter_by(email="userb@example.com").first()
    t_b = db.query(models.Transaction).filter_by(user_id=user_b.user_id).first()
    g_b = db.query(models.BudgetGoal).filter_by(user_id=user_b.user_id).first()
    db.close()

    return {
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"},
        "user_b_tx_id": t_b.transaction_id,
        "user_b_goal_id": g_b.goal_id,
        "user_a_id": user_a.user_id,
        "user_b_id": user_b.user_id
    }


def test_cross_user_transaction_isolation(tokens):
    """User A cannot read, update, or delete User B's transaction via /api/v1 or legacy."""
    h_a = tokens["headers_a"]
    b_tx_id = tokens["user_b_tx_id"]

    # User A tries to GET User B's transaction
    res = client.get(f"/api/v1/transactions/{b_tx_id}", headers=h_a)
    assert res.status_code == 404

    # User A tries to PUT User B's transaction
    res = client.put(f"/api/v1/transactions/{b_tx_id}", json={
        "amount": 1.0,
        "description": "Tampered",
        "category": "food"
    }, headers=h_a)
    assert res.status_code == 404

    # User A tries to DELETE User B's transaction
    res = client.delete(f"/api/v1/transactions/{b_tx_id}", headers=h_a)
    assert res.status_code == 404

    # User A listing transactions never receives User B's data
    list_res = client.get("/api/v1/transactions", headers=h_a)
    assert list_res.status_code == 200
    txns = list_res.json()
    assert all(t["transaction_id"] != b_tx_id for t in txns)
    assert all("Beta Confidential" not in t["description"] for t in txns)

    # Legacy endpoint check
    leg_res = client.get("/transactions", headers=h_a)
    assert leg_res.status_code == 200
    leg_txns = leg_res.json()
    assert all(t["transaction_id"] != b_tx_id for t in leg_txns)


def test_cross_user_goal_isolation(tokens):
    """User A cannot read, update, delete, or pace User B's goal."""
    h_a = tokens["headers_a"]
    b_g_id = tokens["user_b_goal_id"]

    # User A tries to GET User B's goal
    res = client.get(f"/api/v1/goals/{b_g_id}", headers=h_a)
    assert res.status_code == 404

    # User A tries to GET pacing for User B's goal
    res = client.get(f"/api/v1/goals/{b_g_id}/pacing", headers=h_a)
    assert res.status_code == 404

    # User A tries to DELETE User B's goal
    res = client.delete(f"/api/v1/goals/{b_g_id}", headers=h_a)
    assert res.status_code == 404

    # User A listing goals never receives User B's goal
    goals_res = client.get("/api/v1/goals", headers=h_a)
    assert goals_res.status_code == 200
    goals = goals_res.json()
    assert all(g["goal_id"] != b_g_id for g in goals)
    assert all(g["target_amount"] != 50000.0 for g in goals)


def test_cross_user_analytics_and_forecast_isolation(tokens):
    """User A analytics and forecast reflect only User A's numbers."""
    h_a = tokens["headers_a"]

    # Financial overview
    res = client.get("/api/v1/analytics/financial-overview", headers=h_a)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == tokens["user_a_id"]
    assert data["monthly_income"] == 4000.0
    # Spending should be User A's (55.0), not including User B's (999.0)
    assert data["spending"]["total_spent"] == 55.0

    # Forecasting
    f_res = client.get("/api/v1/analytics/forecast", headers=h_a)
    assert f_res.status_code == 200
    f_data = f_res.json()
    assert f_data["user_id"] == tokens["user_a_id"]
    assert f_data["monthly_income"] == 4000.0

    # Layered anomalies
    a_res = client.get("/api/v1/analytics/anomalies/layered", headers=h_a)
    assert a_res.status_code == 200
    a_data = a_res.json()
    assert a_data["user_id"] == tokens["user_a_id"]


def test_cross_user_health_score_and_simulation_isolation(tokens):
    """User A health score and simulation reflect strictly User A's budget and transactions."""
    h_a = tokens["headers_a"]

    # Health score
    res = client.get("/api/v1/analytics/health-score/explainable", headers=h_a)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == tokens["user_a_id"]
    assert "overall_score" in data
    assert "component_scores" in data
    assert data["component_scores"]["savings_surplus"]["rating"] == "Healthy"

    # Purchase simulation
    sim_res = client.post("/api/v1/simulation/purchase", json={
        "purchase_amount": 500.0,
        "purchase_category": "electronics",
        "description": "Laptop upgrade"
    }, headers=h_a)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    # Baseline budget for User A is 2000, current spend 55, new total 555
    assert sim_data["budget_impact"]["monthly_budget"] == 2000.0
    assert sim_data["budget_impact"]["current_spent"] == 55.0
    assert sim_data["budget_impact"]["post_purchase_spent"] == 555.0


def test_cross_user_ai_context_isolation(tokens):
    """AI agent context builder strictly queries User A's tools and data."""
    h_a = tokens["headers_a"]

    # Ask AI directly about spending
    res = client.post("/api/v1/ai/chat", json={
        "message": "How much did I spend this month and what did I buy?"
    }, headers=h_a)
    assert res.status_code == 200
    reply = res.json()["reply"]
    # User B's secret spend of 999 or diamond must never appear
    assert "999" not in reply
    assert "Diamond" not in reply
    assert "Beta" not in reply


def test_cross_user_reports_isolation(tokens):
    """Downloadable and summary reports contain zero User B data."""
    h_a = tokens["headers_a"]

    # Summary data
    res = client.get("/api/v1/analytics/report/summary", headers=h_a)
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["email"] == "usera@example.com"
    assert "userb@example.com" not in json.dumps(data)
    assert "999" not in json.dumps(data)

    # HTML Report
    html_res = client.get("/api/v1/analytics/report/download", headers=h_a)
    assert html_res.status_code == 200
    html = html_res.text
    assert "User Alpha" in html or "usera@example.com" in html
    assert "User Beta" not in html
    assert "Beta Confidential Diamond Purchase" not in html


def test_cross_user_export_and_deletion_isolation(tokens):
    """User A data export only contains User A; deleting User A doesn't delete User B."""
    h_a = tokens["headers_a"]
    h_b = tokens["headers_b"]

    # Export User A
    exp_res = client.get("/api/v1/user/export-data", headers=h_a)
    assert exp_res.status_code == 200
    export_json = exp_res.json()
    assert export_json["user_profile"]["email"] == "usera@example.com"
    assert "password_hash" not in json.dumps(export_json)
    assert "Secret" not in json.dumps(export_json)
    assert "Beta Confidential" not in json.dumps(export_json)

    # Seed a ReceiptPending for User A and User B
    db = TestingSessionLocal()
    r_a = models.ReceiptPending(user_id=tokens["user_a_id"], extracted_data="{}", status="pending")
    r_b = models.ReceiptPending(user_id=tokens["user_b_id"], extracted_data="{}", status="pending")
    db.add_all([r_a, r_b])
    db.commit()
    r_a_id = r_a.receipt_id
    r_b_id = r_b.receipt_id
    db.close()

    # Delete User A
    del_res = client.delete("/api/v1/user/account", headers=h_a)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Verify User A's ReceiptPending was deleted
    db = TestingSessionLocal()
    assert db.query(models.ReceiptPending).filter_by(receipt_id=r_a_id).first() is None
    # Verify User B's ReceiptPending is intact
    assert db.query(models.ReceiptPending).filter_by(receipt_id=r_b_id).first() is not None
    db.close()

    # Verify User B is completely intact
    b_tx_res = client.get(f"/api/v1/transactions/{tokens['user_b_tx_id']}", headers=h_b)
    assert b_tx_res.status_code == 200
    assert b_tx_res.json()["amount"] == 999.0
