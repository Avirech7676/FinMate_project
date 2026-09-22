import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas
import utils
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.user_repo import UserRepository

@dataclass
class IngestionItem:
    amount: float
    description: str
    date: Optional[datetime] = None
    category: Optional[str] = None
    source: str = "manual"
    merchant: Optional[str] = None
    payment_method: Optional[str] = None
    reference_id: Optional[str] = None
    tax: Optional[float] = None
    items: Optional[List[Dict[str, Any]]] = None
    confidence: float = 1.0

@dataclass
class PipelineResult:
    transaction: Optional[models.Transaction] = None
    is_duplicate: bool = False
    status: str = "success"
    reason: Optional[str] = None
    category: str = "other"
    fingerprint: str = ""

class TransactionPipeline:
    """
    Standardized Ingestion Pipeline for all transaction sources:
    Input -> Normalization -> Validation -> Deduplication -> Categorization -> Persistence
    """
    def __init__(self, db: Session):
        self.db = db
        self.txn_repo = TransactionRepository(db)
        self.user_repo = UserRepository(db)

    @staticmethod
    def compute_fingerprint(user_id: int, merchant: str, amount: float, txn_date: datetime) -> str:
        norm_merchant = utils.normalize_merchant_key(merchant or "unknown")
        date_str = txn_date.strftime("%Y-%m-%d") if isinstance(txn_date, (datetime, date)) else "nodate"
        amt_str = f"{abs(amount):.2f}"
        raw = f"{user_id}|{norm_merchant}|{amt_str}|{date_str}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def process_item(
        self,
        user: models.User,
        item: IngestionItem,
        allow_duplicates: bool = False
    ) -> PipelineResult:
        # Step 1: Normalization
        amount = abs(float(item.amount))
        clean_desc = (item.description or "Transaction").strip()
        clean_merchant = item.merchant or utils.normalize_merchant_key(clean_desc)
        txn_date = item.date or datetime.utcnow()

        # Step 2: Validation
        if amount <= 0:
            return PipelineResult(status="rejected", reason="Amount must be positive")
        if amount > 9999999.99:
            return PipelineResult(status="rejected", reason="Amount exceeds supported maximum")

        # Step 3: Deduplication
        fp = self.compute_fingerprint(user.user_id, clean_merchant, amount, txn_date)
        if not allow_duplicates:
            # Check for existing matching transaction within +/- 1 day window with exact same amount and merchant key
            date_min = txn_date.replace(hour=0, minute=0, second=0, microsecond=0)
            candidates = self.txn_repo.get_in_date_range(
                user_id=user.user_id,
                start_date=date_min,
                end_date=txn_date.replace(hour=23, minute=59, second=59)
            )
            for c in candidates:
                c_merchant = utils.normalize_merchant_key(c.description or "")
                if abs(c.amount - amount) < 0.001 and (c_merchant == clean_merchant or c.description == clean_desc):
                    return PipelineResult(
                        is_duplicate=True,
                        status="skipped_duplicate",
                        reason=f"Duplicate of existing transaction #{c.transaction_id}",
                        fingerprint=fp
                    )

        # Step 4: Categorization
        cat = (item.category or "").strip().lower()
        if not cat or cat in {"uncategorized", "other", ""}:
            cat = utils.suggest_category(clean_desc or clean_merchant)

        # Step 5: Persistence
        db_txn = models.Transaction(
            user_id=user.user_id,
            amount=amount,
            category=cat,
            date=txn_date,
            description=clean_desc,
            source=item.source
        )
        created = self.txn_repo.create(db_txn)

        # Update stats
        stats = self.user_repo.get_or_create_stats(user.user_id)
        stats.total_transactions += 1
        stats.total_spending += amount
        self.db.commit()

        # Check achievements
        import gamification
        if stats.total_transactions == 1:
            gamification.check_and_award_achievement(self.db, user, "first_transaction")
        if amount >= 100:
            gamification.check_and_award_achievement(self.db, user, "big_spender")
        if stats.total_transactions >= 50:
            gamification.check_and_award_achievement(self.db, user, "categoric_master")

        return PipelineResult(
            transaction=created,
            is_duplicate=False,
            status="success",
            category=cat,
            fingerprint=fp
        )

    def process_batch(
        self,
        user: models.User,
        items: List[IngestionItem],
        allow_duplicates: bool = False
    ) -> Dict[str, Any]:
        added = 0
        skipped = 0
        categories_count: Dict[str, int] = {}
        txns: List[models.Transaction] = []

        for itm in items:
            res = self.process_item(user, itm, allow_duplicates=allow_duplicates)
            if res.status == "success" and res.transaction:
                added += 1
                txns.append(res.transaction)
                categories_count[res.category] = categories_count.get(res.category, 0) + 1
            elif res.is_duplicate:
                skipped += 1

        return {
            "total_processed": len(items),
            "imported_count": added,
            "duplicates_skipped": skipped,
            "categories_assigned": categories_count,
            "transactions": txns
        }
