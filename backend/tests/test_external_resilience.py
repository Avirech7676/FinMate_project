"""
FinMate 2.0 External Service Resilience Test Suite (Phase 8)
Verifies:
1. Gemini Unavailable -> Graceful deterministic fallback
2. Gemini Timeout -> Graceful deterministic fallback
3. Gemini Quota 429 Failure -> Graceful deterministic fallback
4. Core financial operations (transactions, goals, budgets, analytics, database)
   continue operating completely unimpeded during AI failures
5. External price provider failure -> Graceful degradation
6. Email SMTP service failure -> Graceful handling with zero crashes
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from database import Base
import models
import auth
from app.ai.providers import MockProvider, set_llm_provider
from email_service import EmailService

TEST_DB_URL = "sqlite:///./test_resilience.db"
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
def ensure_resilience_db():
    app.dependency_overrides[get_db] = override_get_db
    yield

@pytest.fixture(scope="module", autouse=True)
def setup_resilience_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    user = models.User(
        email="resilience@example.com",
        password_hash=auth.get_password_hash("ResiliencePass123!"),
        full_name="Resilience Tester",
        currency="USD",
        currency_symbol="$",
        preferences=json.dumps({"monthly_budget": 2000.0})
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    prof = models.FinancialProfile(
        user_id=user.user_id,
        monthly_income=4000.0,
        employment_type="full-time",
        risk_tolerance="moderate"
    )
    db.add(prof)

    txn = models.Transaction(
        user_id=user.user_id,
        amount=50.0,
        category="groceries",
        description="Market Goods",
        date=datetime.utcnow() - timedelta(days=2),
        source="manual"
    )
    db.add(txn)
    db.commit()
    db.close()

    yield

    engine.dispose()
    import os
    if os.path.exists("test_resilience.db"):
        try:
            os.remove("test_resilience.db")
        except Exception:
            pass


@pytest.fixture(scope="module")
def auth_headers():
    app.dependency_overrides[get_db] = override_get_db
    res = client.post("/login", data={"username": "resilience@example.com", "password": "ResiliencePass123!"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_gemini_unavailable_fallback(auth_headers):
    """When Gemini server is unreachable, AI chat falls back to deterministic summary."""
    mock = MockProvider(simulate_error=ConnectionError("Failed to connect to Google Generative Language API"))
    set_llm_provider(mock)

    res = client.post("/api/v1/ai/chat", json={"message": "What is my spend?"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_fallback"] is True
    assert "FinMate Financial Summary" in data["reply"]
    assert "$50.00" in data["reply"]


def test_gemini_timeout_fallback(auth_headers):
    """When Gemini API times out, AI chat activates fallback gracefully without 500 error."""
    mock = MockProvider(simulate_error=TimeoutError("Request to Gemini API timed out after 30000ms"))
    set_llm_provider(mock)

    res = client.post("/api/v1/ai/chat", json={"message": "Analyze my monthly habits", "roast_mode": True}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_fallback"] is True
    assert "burned through" in data["reply"] or "FinMate Financial Summary" in data["reply"]


def test_gemini_quota_exhausted_fallback(auth_headers):
    """When Gemini returns HTTP 429 ResourceExhausted, system provides deterministic advice."""
    mock = MockProvider(simulate_error=Exception("429 Resource has been exhausted (e.g. check quota)"))
    set_llm_provider(mock)

    res = client.post("/api/v1/ai/chat", json={"message": "Give me budget advice"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_fallback"] is True
    assert "Recommendation" in data["reply"]


def test_core_financial_operations_during_complete_ai_outage(auth_headers):
    """
    Even when the AI subsystem is totally broken/unreachable, core financial operations
    (transactions, goals, analytics, health score, purchase simulation) continue running 100%.
    """
    # Simulate total AI failure
    set_llm_provider(MockProvider(simulate_error=RuntimeError("AI subsystem total failure")))

    # 1. Create transaction
    tx_res = client.post("/api/v1/transactions", json={
        "amount": 75.50,
        "category": "utilities",
        "description": "Internet Bill"
    }, headers=auth_headers)
    assert tx_res.status_code == 200
    assert tx_res.json()["amount"] == 75.50

    # 2. List transactions
    list_res = client.get("/api/v1/transactions", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 2

    # 3. Create Goal
    goal_res = client.post("/api/v1/goals", json={
        "goal_type": "savings",
        "target_amount": 2500.0,
        "deadline": (datetime.utcnow() + timedelta(days=60)).isoformat()
    }, headers=auth_headers)
    assert goal_res.status_code == 200
    assert goal_res.json()["target_amount"] == 2500.0

    # 4. Financial Overview Analytics
    ov_res = client.get("/api/v1/analytics/financial-overview", headers=auth_headers)
    assert ov_res.status_code == 200
    assert ov_res.json()["monthly_income"] == 4000.0

    # 5. Explainable Health Score
    hs_res = client.get("/api/v1/analytics/health-score/explainable", headers=auth_headers)
    assert hs_res.status_code == 200
    assert "overall_score" in hs_res.json()

    # 6. Purchase Simulation
    sim_res = client.post("/api/v1/simulation/purchase", json={
        "purchase_amount": 200.0,
        "purchase_category": "shopping"
    }, headers=auth_headers)
    assert sim_res.status_code == 200
    assert sim_res.json()["verdict"] in ["APPROVED", "AFFORDABLE", "CAUTION", "UNRECOMMENDED"]


def test_external_price_provider_resilience():
    """Verify price provider handles network / site scraper failures gracefully."""
    from providers.site_scrapers import AmazonIndiaScraper
    # Mocking network connection error
    with patch("httpx.AsyncClient.get", side_effect=Exception("External price provider DNS failed")):
        scraper = AmazonIndiaScraper()
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(scraper.search(query="noise cancelling headphones", max_results=5))
            # Should return empty result rather than raising an uncaught exception
            assert res.offers == []
            assert res.error is not None
        finally:
            loop.close()


def test_email_service_resilience():
    """Verify email service failure does not crash or interrupt caller."""
    email_svc = EmailService()
    # Configure dummy credentials to trigger send attempt
    email_svc.sender_email = "test@finmate.local"
    email_svc.sender_password = "dummy_password"

    with patch("aiosmtplib.SMTP.connect", side_effect=ConnectionRefusedError("SMTP server down")):
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            success = loop.run_until_complete(
                email_svc.send_notification_email("user@example.com", "Test Subject", "Test Body")
            )
            # Must return False gracefully without raising unhandled exception
            assert success is False
        finally:
            loop.close()
