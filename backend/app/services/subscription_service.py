from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import models
from app.repositories.subscription_repo import SubscriptionRepository

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.sub_repo = SubscriptionRepository(db)

    def record_decision(
        self,
        user_id: int,
        candidate_id: str,
        action: str,
        merchant: str = "",
        avg_amount: float = 0.0,
        interval_days: int = 30,
        occurrences: int = 0,
        last_seen_at: Optional[datetime] = None
    ) -> models.SubscriptionDecision:
        action_internal = "keep" if action.lower() == "keep" else "cancel"
        decision = self.sub_repo.get_decision(user_id, candidate_id)
        if not decision:
            decision = models.SubscriptionDecision(
                user_id=user_id,
                candidate_id=candidate_id,
                merchant=merchant,
                avg_amount=avg_amount,
                interval_days=interval_days,
                occurrences=occurrences,
                last_seen_at=last_seen_at,
                action=action_internal
            )
            return self.sub_repo.create(decision)
        else:
            decision.action = action_internal
            return self.sub_repo.update(decision)

    def list_decisions(self, user_id: int) -> List[models.SubscriptionDecision]:
        return self.sub_repo.list_decisions(user_id)
