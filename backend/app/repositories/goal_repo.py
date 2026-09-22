from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
import models
from app.repositories.base_repo import BaseRepository

class GoalRepository(BaseRepository[models.BudgetGoal]):
    def __init__(self, db: Session):
        super().__init__(models.BudgetGoal, db)

    def get_by_id_and_user(self, goal_id: int, user_id: int) -> Optional[models.BudgetGoal]:
        return self.db.query(models.BudgetGoal).filter(
            models.BudgetGoal.goal_id == goal_id,
            models.BudgetGoal.user_id == user_id
        ).first()

    def list_by_user(self, user_id: int, status: Optional[str] = None) -> List[models.BudgetGoal]:
        query = self.db.query(models.BudgetGoal).filter(models.BudgetGoal.user_id == user_id)
        if status:
            query = query.filter(models.BudgetGoal.status == status)
        return query.order_by(desc(models.BudgetGoal.created_at)).all()

    def get_active(self, user_id: int) -> List[models.BudgetGoal]:
        return self.list_by_user(user_id, status="active")
