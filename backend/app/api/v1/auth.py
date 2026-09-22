from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import auth
from app.services.user_service import UserService

router = APIRouter(prefix="", tags=["auth"])

@router.post("/signup", response_model=schemas.UserOut)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return UserService(db).register_user(user)

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = UserService(db).authenticate_user(form_data.username, form_data.password)
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.get("/user/export-data")
def export_user_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Privacy and data-rights personal data export.
    Returns complete financial history, profile, goals, and preferences
    with all credentials, hashes, and tokens strictly excluded.
    """
    profile = db.query(models.FinancialProfile).filter_by(user_id=current_user.user_id).first()
    transactions = db.query(models.Transaction).filter_by(user_id=current_user.user_id).order_by(models.Transaction.date.desc()).all()
    goals = db.query(models.BudgetGoal).filter_by(user_id=current_user.user_id).all()
    stats = db.query(models.UserStats).filter_by(user_id=current_user.user_id).first()
    achievements = db.query(models.Achievement).filter_by(user_id=current_user.user_id).all()
    subscriptions = db.query(models.SubscriptionDecision).filter_by(user_id=current_user.user_id).all()

    return {
        "export_metadata": {
            "version": "FinMate 2.0 User Data Export",
            "exported_at": str(datetime.utcnow()),
            "user_id": current_user.user_id
        },
        "user_profile": {
            "email": current_user.email,
            "full_name": current_user.full_name,
            "currency": current_user.currency,
            "currency_symbol": current_user.currency_symbol,
            "created_at": str(current_user.created_at),
            "monthly_income": profile.monthly_income if profile else 0.0,
            "employment_type": profile.employment_type if profile else None,
            "risk_tolerance": profile.risk_tolerance if profile else None
        },
        "transactions": [
            {
                "transaction_id": t.transaction_id,
                "amount": t.amount,
                "category": t.category,
                "date": str(t.date),
                "description": t.description,
                "source": t.source
            }
            for t in transactions
        ],
        "goals": [
            {
                "goal_id": g.goal_id,
                "goal_type": g.goal_type,
                "target_amount": g.target_amount,
                "current_progress": g.current_progress,
                "deadline": str(g.deadline),
                "status": g.status
            }
            for g in goals
        ],
        "subscriptions": [
            {
                "merchant": s.merchant,
                "amount": s.avg_amount,
                "interval_days": s.interval_days,
                "action": s.action
            }
            for s in subscriptions
        ],
        "gamification": {
            "total_xp": stats.total_xp if stats else 0,
            "current_streak": stats.current_streak if stats else 0,
            "achievements": [a.title for a in achievements]
        }
    }


@router.delete("/user/account")
def delete_user_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Permanently deletes user account and cascades deletion to all associated
    transactions, budget goals, profile, stats, notifications, and subscription records.
    """
    uid = current_user.user_id
    db.query(models.ReceiptPending).filter_by(user_id=uid).delete()
    db.query(models.Transaction).filter_by(user_id=uid).delete()
    db.query(models.BudgetGoal).filter_by(user_id=uid).delete()
    db.query(models.FinancialProfile).filter_by(user_id=uid).delete()
    db.query(models.UserStats).filter_by(user_id=uid).delete()
    db.query(models.Achievement).filter_by(user_id=uid).delete()
    db.query(models.Notification).filter_by(user_id=uid).delete()
    db.query(models.SubscriptionDecision).filter_by(user_id=uid).delete()
    db.query(models.User).filter_by(user_id=uid).delete()
    db.commit()

    return {
        "status": "success",
        "message": "Account and all associated personal financial data have been permanently deleted."
    }


@router.get("/user/ai-disclosure")
def get_ai_data_disclosure():
    """
    Clear transparency disclosure of external AI processing policy and privacy guarantees.
    """
    return {
        "service": "FinMate 2.0 Financial Intelligence",
        "ai_provider": "Google Gemini (or configured deterministic LLMProvider)",
        "transmitted_data": [
            "Compact aggregated spend metrics (e.g. 30-day totals, category percentages)",
            "Active goal targets and status descriptions",
            "Recent anonymized transaction lines (amount, category, merchant name)",
            "User financial questions and prompts"
        ],
        "strictly_redacted_data": [
            "Passwords and password hashes",
            "JWT bearer tokens and session secrets",
            "Account numbers, routing numbers, and payment cards",
            "API keys and server configurations",
            "Personally identifiable identity documents"
        ],
        "privacy_guarantees": [
            "Cross-user isolation: User context is strictly scoped to the active JWT session.",
            "Token scrubbing: Regex guardrails automatically redact API keys and bearer tokens from LLM outputs.",
            "Deterministic fallback: Core transactions, budgets, goals, and analytics operate even if AI is disconnected.",
            "User right to deletion: Deleting your account immediately purges all stored transactions and profile data."
        ]
    }
