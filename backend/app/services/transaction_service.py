from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
import models
import schemas
import utils
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.user_repo import UserRepository

class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.txn_repo = TransactionRepository(db)
        self.user_repo = UserRepository(db)

    def create_transaction(self, user: models.User, txn_in: schemas.TransactionCreate) -> models.Transaction:
        utils.validate_amount(txn_in.amount)
        category = txn_in.category or "uncategorized"
        if category in {"uncategorized", "other", ""}:
            category = utils.suggest_category(txn_in.description)

        db_txn = models.Transaction(
            user_id=user.user_id,
            amount=txn_in.amount,
            category=category,
            date=txn_in.date or datetime.utcnow(),
            description=txn_in.description,
            source=txn_in.source or "manual"
        )
        created = self.txn_repo.create(db_txn)

        # Update stats
        stats = self.user_repo.get_or_create_stats(user.user_id)
        stats.total_transactions += 1
        stats.total_spending += txn_in.amount
        self.db.commit()

        # Check achievements
        import gamification
        if stats.total_transactions == 1:
            gamification.check_and_award_achievement(self.db, user, "first_transaction")
        if txn_in.amount >= 100:
            gamification.check_and_award_achievement(self.db, user, "big_spender")
        if stats.total_transactions >= 50:
            gamification.check_and_award_achievement(self.db, user, "categoric_master")

        return created

    def list_transactions(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[models.Transaction]:
        return self.txn_repo.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            category=category,
            search=search
        )

    def get_transaction(self, transaction_id: int, user_id: int) -> models.Transaction:
        txn = self.txn_repo.get_by_id_and_user(transaction_id, user_id)
        if not txn:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return txn

    def update_transaction(
        self,
        transaction_id: int,
        user_id: int,
        txn_update: schemas.TransactionCreate
    ) -> models.Transaction:
        txn = self.get_transaction(transaction_id, user_id)
        utils.validate_amount(txn_update.amount)
        
        diff = txn_update.amount - txn.amount
        txn.amount = txn_update.amount
        txn.category = txn_update.category
        txn.description = txn_update.description
        if txn_update.date:
            txn.date = txn_update.date
        
        stats = self.user_repo.get_or_create_stats(user_id)
        stats.total_spending += diff
        return self.txn_repo.update(txn)

    def delete_transaction(self, transaction_id: int, user_id: int) -> dict:
        txn = self.get_transaction(transaction_id, user_id)
        stats = self.user_repo.get_or_create_stats(user_id)
        stats.total_spending -= txn.amount
        stats.total_transactions = max(0, stats.total_transactions - 1)
        self.txn_repo.delete(txn)
        return {"status": "success", "message": "Transaction deleted"}
