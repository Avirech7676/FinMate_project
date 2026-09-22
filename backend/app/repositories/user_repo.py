from typing import Optional
from sqlalchemy.orm import Session
import models
from app.repositories.base_repo import BaseRepository

class UserRepository(BaseRepository[models.User]):
    def __init__(self, db: Session):
        super().__init__(models.User, db)

    def get_by_email(self, email: str) -> Optional[models.User]:
        return self.db.query(models.User).filter(models.User.email == email.strip().lower()).first()

    def get_profile(self, user_id: int) -> Optional[models.FinancialProfile]:
        return self.db.query(models.FinancialProfile).filter(models.FinancialProfile.user_id == user_id).first()

    def get_or_create_stats(self, user_id: int) -> models.UserStats:
        stats = self.db.query(models.UserStats).filter(models.UserStats.user_id == user_id).first()
        if not stats:
            stats = models.UserStats(user_id=user_id)
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)
        return stats
