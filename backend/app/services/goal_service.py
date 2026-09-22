from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
import models
import schemas
from app.repositories.goal_repo import GoalRepository

class GoalService:
    def __init__(self, db: Session):
        self.db = db
        self.goal_repo = GoalRepository(db)

    def create_goal(self, user: models.User, goal_in: schemas.BudgetGoalCreate) -> models.BudgetGoal:
        if goal_in.target_amount <= 0:
            raise HTTPException(status_code=422, detail="Target amount must be positive")
        if goal_in.deadline <= datetime.utcnow():
            raise HTTPException(status_code=422, detail="Deadline must be in the future")

        goal = models.BudgetGoal(
            user_id=user.user_id,
            goal_type=goal_in.goal_type,
            target_amount=goal_in.target_amount,
            deadline=goal_in.deadline,
            current_progress=0.0,
            status="active"
        )
        created = self.goal_repo.create(goal)
        try:
            import gamification
            gamification.create_notification(
                self.db,
                user.user_id,
                "Goal Created!",
                f"You set a {goal_in.goal_type} goal for ${goal_in.target_amount:.2f}",
                "achievement"
            )
        except Exception:
            pass
        return created

    def list_goals(self, user_id: int, status: Optional[str] = None) -> List[models.BudgetGoal]:
        return self.goal_repo.list_by_user(user_id, status=status)

    def get_goal(self, goal_id: int, user_id: int) -> models.BudgetGoal:
        goal = self.goal_repo.get_by_id_and_user(goal_id, user_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal

    def update_goal(
        self,
        goal_id: int,
        user_id: int,
        goal_update: schemas.BudgetGoalUpdate | schemas.BudgetGoalCreate
    ) -> models.BudgetGoal:
        goal = self.get_goal(goal_id, user_id)
        update_data = goal_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(goal, key, value)
        return self.goal_repo.update(goal)

    def delete_goal(self, goal_id: int, user_id: int) -> dict:
        goal = self.get_goal(goal_id, user_id)
        self.goal_repo.delete(goal)
        return {"status": "success", "message": "Goal deleted"}
