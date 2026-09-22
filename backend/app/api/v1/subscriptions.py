from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
import auth
from app.services.subscription_service import SubscriptionService
from app.repositories.transaction_repo import TransactionRepository
from app.analytics.subscriptions import SubscriptionIntelligenceEngine

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.get("/intelligence")
def get_subscription_intelligence(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Detect recurring/subscription expenses and calculate annualized costs."""
    txn_repo = TransactionRepository(db)
    sub_service = SubscriptionService(db)

    # Fetch last 180 days of transactions
    txns = txn_repo.get_in_date_range(
        current_user.user_id,
        datetime.utcnow() - timedelta(days=180),
        datetime.utcnow()
    )
    user_decisions = {d.candidate_id: d.action for d in sub_service.list_decisions(current_user.user_id)}
    candidates = SubscriptionIntelligenceEngine.detect_subscriptions(txns, current_user.user_id, user_decisions)

    total_annualized = sum(c.annualized_cost for c in candidates if user_decisions.get(c.candidate_id) != "cancel")
    monthly_leak = total_annualized / 12.0

    return {
        "user_id": current_user.user_id,
        "total_subscriptions": len(candidates),
        "total_annualized_cost": round(total_annualized, 2),
        "estimated_monthly_leak": round(monthly_leak, 2),
        "subscriptions": [
            {
                "candidate_id": c.candidate_id,
                "merchant": c.merchant,
                "amount": c.amount,
                "frequency": c.frequency,
                "interval_days": c.interval_days,
                "occurrences": c.occurrences,
                "confidence": c.confidence,
                "annualized_cost": c.annualized_cost,
                "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None,
                "category": c.category,
                "user_decision": user_decisions.get(c.candidate_id, "pending")
            }
            for c in candidates
        ]
    }

@router.post("/suspects/{candidate_id}/decision")
def set_subscription_suspect_decision(
    candidate_id: str,
    req: schemas.SubscriptionSuspectDecisionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    sub_service = SubscriptionService(db)
    decision = sub_service.record_decision(
        user_id=current_user.user_id,
        candidate_id=candidate_id,
        action=req.decision
    )
    return {"status": "success", "decision": req.decision}

@router.get("/decisions", response_model=List[schemas.SubscriptionSuspectOut])
def list_subscription_decisions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    decisions = SubscriptionService(db).list_decisions(current_user.user_id)
    return [
        schemas.SubscriptionSuspectOut(
            candidate_id=d.candidate_id,
            merchant=d.merchant or "",
            avg_amount=d.avg_amount or 0.0,
            interval_days=d.interval_days or 30,
            occurrences=d.occurrences or 0,
            last_seen_at=d.last_seen_at.isoformat() if d.last_seen_at else None,
            decision=d.action
        )
        for d in decisions
    ]
