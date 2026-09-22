import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from main import app, get_db
from database import Base


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


TEST_USER_PASSWORD = "TestPassword123"


def _signup_and_login(email: str):
    client.post("/signup", json={"email": email, "password": TEST_USER_PASSWORD, "full_name": "Test User"})
    res = client.post("/login", data={"username": email, "password": TEST_USER_PASSWORD})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestDebateMode:
    def test_debate_offers_partial_failure_ok(self, monkeypatch):
        """
        Even if one provider fails, the endpoint must still return 200 with partial offers.
        """
        headers = _signup_and_login("debate1@example.com")

        from providers import web_search
        from providers.base import ProviderResult
        import schemas as _schemas

        class OkProvider:
            name = "web"

            async def search(self, *, query: str, max_results: int, location=None, timeout_s: float = 4.0):
                return ProviderResult(
                    provider="web",
                    offers=[
                        _schemas.OfferOut(
                            provider="web",
                            title="Test Offer",
                            price=99.0,
                            currency="INR",
                            url="https://example.com",
                        )
                    ],
                    error=None,
                )

        class BadProvider:
            name = "amazon"

            async def search(self, *, query: str, max_results: int, location=None, timeout_s: float = 4.0):
                raise RuntimeError("boom")

        monkeypatch.setattr(web_search, "default_offer_providers", lambda: [BadProvider(), OkProvider()])

        res = client.post(
            "/debate/offers",
            json={"query": "rice 5kg", "priority": "best_overall", "max_results": 5},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == "rice 5kg"
        assert isinstance(data["offers"], list)
        assert len(data["offers"]) >= 1
        assert "errors_by_provider" in data

    def test_debate_run_returns_roles(self):
        headers = _signup_and_login("debate2@example.com")
        res = client.post(
            "/debate/run",
            json={"query": "wireless mouse", "priority": "cheapest", "max_results": 3},
            headers=headers,
        )
        # We don't assert offers exist (network dependent); but roles should exist and response shape should be stable.
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == "wireless mouse"
        assert "roles" in data and isinstance(data["roles"], list)
        assert len(data["roles"]) == 4
        assert "final_recommendation" in data

