from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
import models
import auth
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.user_repo import UserRepository
from app.repositories.goal_repo import GoalRepository
from app.analytics.cashflow import CashFlowEngine

router = APIRouter(prefix="/cashflow", tags=["cashflow"])

@router.get("/projection")
def get_cashflow_projection(
    initial_balance: float = Query(0.0, ge=0.0),
    days_forward: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    txn_repo = TransactionRepository(db)
    user_repo = UserRepository(db)
    goal_repo = GoalRepository(db)

    profile = user_repo.get_profile(current_user.user_id)
    monthly_income = float(profile.monthly_income or 0.0) if profile else 0.0
    
    # 90 days history for recurring patterns
    txns = txn_repo.get_in_date_range(
        current_user.user_id,
        datetime.utcnow() - timedelta(days=90),
        datetime.utcnow()
    )
    goals = goal_repo.list_by_user(current_user.user_id)

    projection = CashFlowEngine.calculate_cashflow(
        user=current_user,
        monthly_income=monthly_income,
        transactions=txns,
        goals=goals,
        initial_balance=initial_balance,
        days_forward=days_forward
    )
    return {
        "user_id": current_user.user_id,
        "currency": current_user.currency,
        "currency_symbol": current_user.currency_symbol,
        **projection
    }
