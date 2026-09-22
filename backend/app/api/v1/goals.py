from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import auth
from app.services.goal_service import GoalService
from app.analytics.goals import GoalPacingEngine

router = APIRouter(prefix="/goals", tags=["goals"])

@router.post("", response_model=schemas.BudgetGoalOut)
def create_goal(
    goal: schemas.BudgetGoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return GoalService(db).create_goal(current_user, goal)

@router.get("", response_model=List[schemas.BudgetGoalOut])
def get_goals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return GoalService(db).list_goals(current_user.user_id)

@router.get("/pacing")
def get_all_goals_pacing(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get pacing and progress analytics for all active goals.
    """
    goals = GoalService(db).list_goals(current_user.user_id)
    results = []
    for g in goals:
        evaluation = GoalPacingEngine.evaluate_goal(
            target_amount=g.target_amount,
            current_progress=g.current_progress or 0.0,
            deadline=g.deadline,
            created_at=g.created_at,
            goal_type=g.goal_type or "savings"
        )
        evaluation["goal_id"] = g.goal_id
        evaluation["goal_type"] = g.goal_type
        results.append(evaluation)
    return results

@router.get("/{goal_id}/pacing")
def get_goal_pacing(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get detailed pacing calculation for a specific goal.
    """
    goal = GoalService(db).get_goal(goal_id, current_user.user_id)
    evaluation = GoalPacingEngine.evaluate_goal(
        target_amount=goal.target_amount,
        current_progress=goal.current_progress or 0.0,
        deadline=goal.deadline,
        created_at=goal.created_at,
        goal_type=goal.goal_type or "savings"
    )
    evaluation["goal_id"] = goal.goal_id
    evaluation["goal_type"] = goal.goal_type
    return evaluation

@router.get("/{goal_id}", response_model=schemas.BudgetGoalOut)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return GoalService(db).get_goal(goal_id, current_user.user_id)

@router.put("/{goal_id}", response_model=schemas.BudgetGoalOut)
def update_goal(
    goal_id: int,
    goal: schemas.BudgetGoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return GoalService(db).update_goal(goal_id, current_user.user_id, goal)

@router.delete("/{goal_id}")
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return GoalService(db).delete_goal(goal_id, current_user.user_id)
