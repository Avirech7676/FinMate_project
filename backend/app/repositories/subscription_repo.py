from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
import models
from app.repositories.base_repo import BaseRepository

class SubscriptionRepository(BaseRepository[models.SubscriptionDecision]):
    def __init__(self, db: Session):
        super().__init__(models.SubscriptionDecision, db)

    def get_decision(self, user_id: int, candidate_id: str) -> Optional[models.SubscriptionDecision]:
        return self.db.query(models.SubscriptionDecision).filter(
            models.SubscriptionDecision.user_id == user_id,
            models.SubscriptionDecision.candidate_id == candidate_id
        ).first()

    def list_decisions(self, user_id: int) -> List[models.SubscriptionDecision]:
        return self.db.query(models.SubscriptionDecision).filter(
            models.SubscriptionDecision.user_id == user_id
        ).order_by(desc(models.SubscriptionDecision.created_at)).all()
