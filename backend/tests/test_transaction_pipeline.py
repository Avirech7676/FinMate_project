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
from app.services.transaction_pipeline import TransactionPipeline, IngestionItem
from app.services.csv_service import CSVImportService
from app.services.ocr_service import ReceiptOCRService

TEST_DB_URL = "sqlite:///./test_pipeline.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    try:
        if os.path.exists("test_pipeline.db"):
            os.remove("test_pipeline.db")
    except Exception:
        pass

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_pipeline_deduplication(db_session):
    user_svc = UserService(db_session)
    user = user_svc.register_user(schemas.UserCreate(
        email="pipeline_tester@example.com",
        password="PipelinePassword123",
        full_name="Pipeline Tester"
    ))

    pipeline = TransactionPipeline(db_session)
    now = datetime(2026, 9, 20, 14, 30)

    # First entry
    item1 = IngestionItem(
        amount=34.99,
        description="Netflix Subscription",
        date=now,
        source="manual"
    )
    res1 = pipeline.process_item(user, item1)
    assert res1.status == "success"
    assert res1.is_duplicate is False
    assert res1.category == "entertainment"
    assert res1.transaction.amount == 34.99

    # Identical entry (duplicate)
    item2 = IngestionItem(
        amount=34.99,
        description="Netflix Subscription",
        date=now,
        source="import"
    )
    res2 = pipeline.process_item(user, item2, allow_duplicates=False)
    assert res2.is_duplicate is True
    assert res2.status == "skipped_duplicate"

def test_csv_import_with_pipeline(db_session):
    user_svc = UserService(db_session)
    user = user_svc.user_repo.get_by_email("pipeline_tester@example.com")

    csv_svc = CSVImportService(db_session)
    csv_bytes = (
        b"Date,Description,Amount\n"
        b"2026-09-21,Uber Ride,18.50\n"
        b"2026-09-21,Uber Ride,18.50\n"  # Duplicate row
        b"2026-09-22,Whole Foods Groceries,92.10\n"
    )

    # Preview
    preview = csv_svc.preview_csv(csv_bytes)
    assert preview["total_rows"] == 3
    assert len(preview["sample_rows"]) == 3

    # Import
    result = csv_svc.import_csv_data(csv_bytes, user)
    assert result["imported"] == 2
    assert result["duplicates_skipped"] == 1

def test_ocr_staging_and_confirmation(db_session):
    user_svc = UserService(db_session)
    user = user_svc.user_repo.get_by_email("pipeline_tester@example.com")

    ocr_svc = ReceiptOCRService(db_session)
    mock_extracted = {
        "merchant": "Trader Joe's",
        "total": 42.15,
        "amount": 42.15,
        "category": "food",
        "date": "2026-09-22",
        "tax": 3.50,
        "items": [{"name": "Bananas", "price": 1.29}],
        "payment_method": "Visa",
        "confidence": 0.95
    }

    pending = ocr_svc.stage_receipt(user.user_id, mock_extracted)
    assert pending.receipt_id is not None
    assert pending.status == "pending"

    # Confirm
    confirm_req = schemas.ReceiptConfirmRequest(
        receipt_id=pending.receipt_id,
        confirmed=True,
        amount=42.15,
        category="food",
        description="Trader Joe's Groceries"
    )
    txn = ocr_svc.confirm_receipt(pending.receipt_id, user, confirm_req)
    assert txn is not None
    assert txn.amount == 42.15
    assert txn.source == "receipt"
