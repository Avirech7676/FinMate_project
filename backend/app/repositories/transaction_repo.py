from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
import models
from app.repositories.base_repo import BaseRepository

class TransactionRepository(BaseRepository[models.Transaction]):
    def __init__(self, db: Session):
        super().__init__(models.Transaction, db)

    def get_by_id_and_user(self, transaction_id: int, user_id: int) -> Optional[models.Transaction]:
        return self.db.query(models.Transaction).filter(
            models.Transaction.transaction_id == transaction_id,
            models.Transaction.user_id == user_id
        ).first()

    def list_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[models.Transaction]:
        query = self.db.query(models.Transaction).filter(models.Transaction.user_id == user_id)
        if category and category.lower() != "all":
            query = query.filter(models.Transaction.category == category.lower())
        if search:
            query = query.filter(models.Transaction.description.ilike(f"%{search}%"))
        return query.order_by(desc(models.Transaction.date)).offset(offset).limit(limit).all()

    def get_in_date_range(self, user_id: int, start_date: datetime, end_date: datetime) -> List[models.Transaction]:
        return self.db.query(models.Transaction).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.date >= start_date,
            models.Transaction.date < end_date
        ).order_by(desc(models.Transaction.date)).all()

    def get_recent(self, user_id: int, limit: int = 20) -> List[models.Transaction]:
        return self.db.query(models.Transaction).filter(
            models.Transaction.user_id == user_id
        ).order_by(desc(models.Transaction.date)).limit(limit).all()

    def count_by_user(self, user_id: int) -> int:
        return self.db.query(models.Transaction).filter(models.Transaction.user_id == user_id).count()
