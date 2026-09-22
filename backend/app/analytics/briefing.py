"""
FinMate 2.0 Weekly Financial Briefing Engine
Generates structured, deterministic weekly financial summaries and actionable suggestions.
All numerical values are computed exclusively from database records.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import models
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.goal_repo import GoalRepository
from app.repositories.user_repo import UserRepository
from app.analytics.spending import SpendingAnalytics
from app.analytics.anomalies import LayeredAnomalyDetector
from app.analytics.forecasting import SpendingForecaster
from app.analytics.goals import GoalPacingEngine
from app.analytics.health_score import ExplainableHealthScoreEngine
from app.analytics.subscriptions import SubscriptionIntelligenceEngine


class WeeklyBriefingEngine:
    @staticmethod
    def generate_briefing(db: Session, user: models.User) -> Dict[str, Any]:
        now = datetime.utcnow()
        txn_repo = TransactionRepository(db)
        goal_repo = GoalRepository(db)
        user_repo = UserRepository(db)

        # 1. Windows: This week (last 7 days) vs Prior week (7-14 days ago)
        start_this_week = now - timedelta(days=7)
        start_prior_week = now - timedelta(days=14)

        this_week_txns = txn_repo.get_in_date_range(user.user_id, start_this_week, now)
        prior_week_txns = txn_repo.get_in_date_range(user.user_id, start_prior_week, start_this_week)

        this_week_spent = sum(t.amount for t in this_week_txns)
        prior_week_spent = sum(t.amount for t in prior_week_txns)

        # Spending change
        if prior_week_spent > 0:
            pct_change = round(((this_week_spent - prior_week_spent) / prior_week_spent) * 100.0, 1)
        else:
            pct_change = 0.0

        # 2. Largest spending categories this week
        cat_map: Dict[str, float] = {}
        for t in this_week_txns:
            cat = t.category or "other"
            cat_map[cat] = cat_map.get(cat, 0.0) + t.amount
        top_cats = sorted(
            [{"category": k, "amount": round(v, 2)} for k, v in cat_map.items()],
            key=lambda x: x["amount"],
            reverse=True
        )[:4]

        # 3. Profile and budget
        profile = user_repo.get_profile(user.user_id)
        monthly_income = float(profile.monthly_income or 0.0) if profile else 0.0
        monthly_budget = float(user.monthly_budget or 0.0) if hasattr(user, "monthly_budget") and user.monthly_budget else 0.0

        # Month-to-date spending
        start_month = datetime(now.year, now.month, 1)
        month_txns = txn_repo.get_in_date_range(user.user_id, start_month, now)
        month_spent = sum(t.amount for t in month_txns)

        # 4. Anomalies
        anomalies = LayeredAnomalyDetector.detect_anomalies(this_week_txns, monthly_income=monthly_income)

        # 5. Goal progress
        goals = goal_repo.list_by_user(user.user_id)
        goal_summaries = []
        for g in goals:
            eval_g = GoalPacingEngine.evaluate_goal(
                g.target_amount, g.current_progress or 0.0, g.deadline, g.created_at
            )
            goal_summaries.append({
                "goal_id": g.goal_id,
                "target_amount": g.target_amount,
                "current_progress": g.current_progress,
                "status": eval_g["status"],
                "explanation": eval_g["explanation"]
            })

        # 6. Forecast & Upcoming recurring
        forecast_res = SpendingForecaster.generate_forecast(month_txns, monthly_income=monthly_income)
        detected_subs = SubscriptionIntelligenceEngine.detect_subscriptions(month_txns, user_id=user.user_id)

        # 7. Actionable Suggestions (Deterministic)
        suggestions = []
        if pct_change > 15.0:
            suggestions.append(f"Spending spiked +{pct_change}% compared to last week. Review top category: {top_cats[0]['category'] if top_cats else 'discretionary'}.")
        elif pct_change < -10.0:
            suggestions.append(f"Great pacing! Your spending decreased by {abs(pct_change)}% this week.")

        if monthly_budget > 0 and month_spent > monthly_budget * 0.8:
            suggestions.append(f"Monthly budget utilization reached {round(month_spent / monthly_budget * 100, 1)}%. Tighten discretionary expenses.")

        if any(g["status"] == "BEHIND" for g in goal_summaries):
            suggestions.append("At least one financial goal is behind schedule. Consider reallocating surplus funds.")

        if not suggestions:
            suggestions.append("Your financial habits are steady and within healthy parameters for this cycle.")

        return {
            "period": {
                "start": start_this_week.strftime("%Y-%m-%d"),
                "end": now.strftime("%Y-%m-%d")
            },
            "spending": {
                "this_week_spent": round(this_week_spent, 2),
                "prior_week_spent": round(prior_week_spent, 2),
                "week_over_week_change_pct": pct_change
            },
            "largest_categories": top_cats,
            "unusual_transactions": [
                {"id": a.transaction_id, "score": a.anomaly_score, "reason": a.reason}
                for a in anomalies
            ],
            "budget_status": {
                "monthly_budget": monthly_budget,
                "month_to_date_spent": round(month_spent, 2),
                "remaining": max(0.0, round(monthly_budget - month_spent, 2)) if monthly_budget > 0 else 0.0
            },
            "goal_progress": goal_summaries,
            "upcoming_recurring_expenses": detected_subs[:4],
            "forecast_30d": forecast_res.get("30d", {}).get("projected_spending"),
            "actionable_suggestions": suggestions
        }
