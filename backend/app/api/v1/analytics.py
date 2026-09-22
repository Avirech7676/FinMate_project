from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
import models
import auth
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.goal_repo import GoalRepository
from app.repositories.user_repo import UserRepository
from app.analytics.spending import SpendingAnalytics
from app.analytics.rules import FinancialRuleEngine
from app.analytics.anomalies import LayeredAnomalyDetector
from app.analytics.forecasting import SpendingForecaster
from app.analytics.health_score import ExplainableHealthScoreEngine
from app.analytics.goals import GoalPacingEngine

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/financial-overview")
def get_financial_overview(
    month_offset: int = Query(0, ge=-12, le=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    txn_repo = TransactionRepository(db)
    user_repo = UserRepository(db)
    goal_repo = GoalRepository(db)

    # Current month window
    now = datetime.utcnow()
    y = now.year
    m = now.month + month_offset
    while m <= 0:
        y -= 1
        m += 12
    start_curr = datetime(y, m, 1)
    end_m = m + 1
    end_y = y
    if end_m == 13:
        end_m = 1
        end_y += 1
    end_curr = datetime(end_y, end_m, 1)

    # Prior month window
    pm = m - 1
    py = y
    if pm == 0:
        pm = 12
        py -= 1
    start_prior = datetime(py, pm, 1)
    end_prior = start_curr

    curr_txns = txn_repo.get_in_date_range(current_user.user_id, start_curr, end_curr)
    prior_txns = txn_repo.get_in_date_range(current_user.user_id, start_prior, end_prior)
    profile = user_repo.get_profile(current_user.user_id)
    monthly_income = float(profile.monthly_income or 0.0) if profile else 0.0
    goals = goal_repo.list_by_user(current_user.user_id)

    spending_summary = SpendingAnalytics.compute_spending_summary(curr_txns)
    monthly_comparison = SpendingAnalytics.compute_monthly_comparison(curr_txns, prior_txns)
    rules_evaluated = FinancialRuleEngine.evaluate_all(
        user=current_user,
        current_month_spending=spending_summary["total_spent"],
        monthly_income=monthly_income,
        goals=goals,
        recent_transactions=curr_txns
    )

    return {
        "user_id": current_user.user_id,
        "currency": current_user.currency,
        "currency_symbol": current_user.currency_symbol,
        "monthly_income": monthly_income,
        "spending": spending_summary,
        "comparison": monthly_comparison,
        "signals": [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "severity": r.severity,
                "message": r.message,
                "evidence": r.evidence
            }
            for r in rules_evaluated
        ]
    }

@router.get("/anomalies/layered")
def get_layered_anomalies(
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """3-Tier Layered Anomaly Detection (Rule, Statistical, ML Isolation Forest)."""
    txn_repo = TransactionRepository(db)
    user_repo = UserRepository(db)

    start_date = datetime.utcnow() - timedelta(days=days)
    txns = txn_repo.get_in_date_range(current_user.user_id, start_date, datetime.utcnow())
    profile = user_repo.get_profile(current_user.user_id)
    monthly_income = float(profile.monthly_income or 0.0) if profile else 0.0

    anomalies = LayeredAnomalyDetector.detect_anomalies(txns, monthly_income=monthly_income)
    return {
        "user_id": current_user.user_id,
        "total_anomalies": len(anomalies),
        "anomalies": [
            {
                "transaction_id": a.transaction_id,
                "anomaly_score": a.anomaly_score,
                "severity": a.severity,
                "level": a.level,
                "reason": a.reason,
                "evidence": a.evidence
            }
            for a in anomalies
        ]
    }

@router.get("/forecast")
def get_spending_forecast(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Spending, savings, and cash flow forecast for 7-day, 30-day, and 90-day horizons."""
    txn_repo = TransactionRepository(db)
    user_repo = UserRepository(db)

    start_date = datetime.utcnow() - timedelta(days=180)
    txns = txn_repo.get_in_date_range(current_user.user_id, start_date, datetime.utcnow())
    profile = user_repo.get_profile(current_user.user_id)
    monthly_income = float(profile.monthly_income or 0.0) if profile else 0.0

    forecast = SpendingForecaster.generate_forecast(txns, monthly_income=monthly_income)
    return {
        "user_id": current_user.user_id,
        "currency": current_user.currency,
        "currency_symbol": current_user.currency_symbol,
        "monthly_income": monthly_income,
        **forecast
    }

@router.get("/health-score/explainable")
def get_explainable_health_score(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Explainable multi-factor financial health score with weighted component breakdown.
    """
    txn_repo = TransactionRepository(db)
    user_repo = UserRepository(db)
    goal_repo = GoalRepository(db)

    profile = user_repo.get_profile(current_user.user_id)
    monthly_income = float(profile.monthly_income or 0.0) if profile else 0.0
    monthly_budget = float(current_user.monthly_budget or 0.0) if current_user.monthly_budget else None

    # Get last 30 days transactions for spending and consistency
    start_30d = datetime.utcnow() - timedelta(days=30)
    txns_30d = txn_repo.get_in_date_range(current_user.user_id, start_30d, datetime.utcnow())
    total_spent_30d = sum(t.amount for t in txns_30d)

    # Group daily spending
    daily_spend_map = {}
    for t in txns_30d:
        d_str = t.date.strftime("%Y-%m-%d")
        daily_spend_map[d_str] = daily_spend_map.get(d_str, 0.0) + t.amount
    daily_spending_history = list(daily_spend_map.values())

    # Get goals status
    goals = goal_repo.list_by_user(current_user.user_id)
    goal_statuses = []
    for g in goals:
        eval_g = GoalPacingEngine.evaluate_goal(
            target_amount=g.target_amount,
            current_progress=g.current_progress or 0.0,
            deadline=g.deadline,
            created_at=g.created_at
        )
        goal_statuses.append(eval_g["status"])

    # Anomalies in last 30 days
    anomalies = LayeredAnomalyDetector.detect_anomalies(txns_30d, monthly_income=monthly_income)

    result = ExplainableHealthScoreEngine.calculate(
        monthly_income=monthly_income,
        monthly_spending=total_spent_30d,
        monthly_budget=monthly_budget,
        daily_spending_history=daily_spending_history,
        goal_statuses=goal_statuses,
        anomaly_count=len(anomalies)
    )

    return {
        "user_id": current_user.user_id,
        "currency": current_user.currency,
        "currency_symbol": current_user.currency_symbol,
        **result
    }

from fastapi.responses import HTMLResponse
from app.analytics.briefing import WeeklyBriefingEngine
from app.analytics.reports import FinancialReportService

@router.get("/briefing/weekly")
def get_weekly_briefing(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get structured weekly financial briefing and suggestions."""
    return WeeklyBriefingEngine.generate_briefing(db, current_user)

@router.get("/report/summary")
def get_report_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Structured financial report summary data."""
    return FinancialReportService.generate_report_data(db, current_user)

@router.get("/report/download", response_class=HTMLResponse)
def download_html_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Download or print sanitized HTML/PDF financial report."""
    return FinancialReportService.generate_html_report(db, current_user)
