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
from app.services.transaction_service import TransactionService
from app.services.goal_service import GoalService
from app.services.subscription_service import SubscriptionService

TEST_DB_URL = "sqlite:///./test_services.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    try:
        if os.path.exists("test_services.db"):
            os.remove("test_services.db")
    except Exception:
        pass

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_user_service_registration_and_auth(db_session):
    user_svc = UserService(db_session)
    user_in = schemas.UserCreate(
        email="service_test@example.com",
        password="SecurePassword123",
        full_name="Service Tester"
    )
    user = user_svc.register_user(user_in)
    assert user.user_id is not None
    assert user.email == "service_test@example.com"
    assert user.currency == "USD"

    # Authenticate
    auth_user = user_svc.authenticate_user("service_test@example.com", "SecurePassword123")
    assert auth_user.user_id == user.user_id

def test_transaction_service_crud(db_session):
    user_svc = UserService(db_session)
    user = user_svc.user_repo.get_by_email("service_test@example.com")

    txn_svc = TransactionService(db_session)
    txn_in = schemas.TransactionCreate(
        amount=75.50,
        description="Blue Tokai Coffee",
        category="uncategorized"
    )
    created = txn_svc.create_transaction(user, txn_in)
    assert created.transaction_id is not None
    assert created.category == "food"
    assert created.amount == 75.50

    # List
    txns = txn_svc.list_transactions(user.user_id)
    assert len(txns) >= 1

    # Update
    updated = txn_svc.update_transaction(
        created.transaction_id,
        user.user_id,
        schemas.TransactionCreate(amount=80.0, description="Blue Tokai Specialty Coffee", category="food")
    )
    assert updated.amount == 80.0

    # Delete
    del_res = txn_svc.delete_transaction(created.transaction_id, user.user_id)
    assert del_res["status"] == "success"

def test_goal_service_lifecycle(db_session):
    user_svc = UserService(db_session)
    user = user_svc.user_repo.get_by_email("service_test@example.com")

    goal_svc = GoalService(db_session)
    future = datetime.utcnow() + timedelta(days=60)
    goal_in = schemas.BudgetGoalCreate(
        goal_type="savings",
        target_amount=5000.0,
        deadline=future
    )
    goal = goal_svc.create_goal(user, goal_in)
    assert goal.goal_id is not None
    assert goal.status == "active"

    goals = goal_svc.list_goals(user.user_id)
    assert len(goals) >= 1

    del_res = goal_svc.delete_goal(goal.goal_id, user.user_id)
    assert del_res["status"] == "success"

def test_subscription_service(db_session):
    user_svc = UserService(db_session)
    user = user_svc.user_repo.get_by_email("service_test@example.com")

    sub_svc = SubscriptionService(db_session)
    cand_id = "cand_12345"
    decision = sub_svc.record_decision(
        user_id=user.user_id,
        candidate_id=cand_id,
        action="keep",
        merchant="Spotify",
        avg_amount=10.99
    )
    assert decision.decision_id is not None
    assert decision.action == "keep"

    decisions = sub_svc.list_decisions(user.user_id)
    assert len(decisions) >= 1
