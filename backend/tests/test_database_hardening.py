"""
FinMate 2.0 Database Hardening & Session Lifecycle Tests (Phase 9)
Verifies:
1. Automatic rollback on transaction failure / integrity error
2. Session properly closed after request completion via get_db dependency
3. Clean Alembic schema creation and upgrade verification
"""

import pytest
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from database import Base, get_db
import models
from alembic.config import Config
from alembic import command

TEST_DB_URL = "sqlite:///./test_db_hardening.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if os.path.exists("test_db_hardening.db"):
        try:
            os.remove("test_db_hardening.db")
        except Exception:
            pass


def test_transaction_rollback_on_integrity_error():
    """Verify that when a database write fails, session.rollback() prevents dirty state."""
    session = TestingSessionLocal()
    # 1. Insert valid user
    u1 = models.User(email="unique_test@example.com", password_hash="hash1", currency="USD")
    session.add(u1)
    session.commit()

    # 2. Try inserting duplicate user with identical unique email
    u2 = models.User(email="unique_test@example.com", password_hash="hash2", currency="USD")
    session.add(u2)
    with pytest.raises(IntegrityError):
        session.commit()

    # Rollback must successfully clear the failed state
    session.rollback()

    # Verify session is clean and can perform normal queries
    count = session.query(models.User).filter_by(email="unique_test@example.com").count()
    assert count == 1

    # Insert next item successfully
    u3 = models.User(email="second_user@example.com", password_hash="hash3", currency="USD")
    session.add(u3)
    session.commit()
    assert u3.user_id is not None
    session.close()


def test_get_db_session_lifecycle_and_closing():
    """Verify get_db generator properly opens, yields, and closes session."""
    db_gen = get_db()
    session = next(db_gen)
    assert session is not None
    assert session.is_active is True

    # Closing generator must execute the finally block closing the session
    try:
        next(db_gen)
    except StopIteration:
        pass

    # In SQLAlchemy, after close(), session transaction is ended
    assert not session.in_transaction()


def test_alembic_clean_migration_cycle():
    """Verify Alembic upgrade works cleanly on a fresh database."""
    db_file = "test_alembic_cycle.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

    fresh_db = f"sqlite:///./{db_file}"
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", fresh_db)

    # Run upgrade head
    command.upgrade(alembic_cfg, "head")

    # Verify table existence in fresh DB
    test_engine = create_engine(fresh_db)
    from sqlalchemy import inspect
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "transactions" in tables
    assert "budget_goals" in tables
    assert "financial_profiles" in tables
    test_engine.dispose()

    if os.path.exists("test_alembic_cycle.db"):
        try:
            os.remove("test_alembic_cycle.db")
        except Exception:
            pass
