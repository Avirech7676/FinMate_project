import pytest
import os
import sys
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base
import models
import auth

TEST_DB_URL = "sqlite:///./test_shared.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_shared_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    try:
        if os.path.exists("test_shared.db"):
            os.remove("test_shared.db")
    except Exception:
        pass

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def test_user(db_session):
    user = db_session.query(models.User).filter_by(email="ai_test@example.com").first()
    if not user:
        user = models.User(
            email="ai_test@example.com",
            password_hash=auth.get_password_hash("SecretPassword123!"),
            currency="USD",
            currency_symbol="$",
            preferences=json.dumps({"monthly_budget": 2500.0})
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        profile = models.FinancialProfile(
            user_id=user.user_id,
            monthly_income=5000.0,
            employment_type="full-time",
            risk_tolerance="moderate"
        )
        db_session.add(profile)
        db_session.commit()
    return user
