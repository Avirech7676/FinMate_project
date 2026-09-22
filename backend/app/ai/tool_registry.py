"""
FinMate 2.0 Controlled AI Tool Registry
Provides whitelisted, deterministic financial calculation tools to the AI agent.
Strictly scoped to the authenticated user ID.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.goal_repo import GoalRepository
from app.repositories.user_repo import UserRepository
from app.analytics.spending import SpendingAnalytics
from app.analytics.anomalies import LayeredAnomalyDetector
from app.analytics.forecasting import SpendingForecaster
from app.analytics.cashflow import CashFlowEngine
from app.analytics.subscriptions import SubscriptionIntelligenceEngine
from app.analytics.goals import GoalPacingEngine
from app.analytics.health_score import ExplainableHealthScoreEngine


class ToolRegistry:
    """
    Controlled registry of tools callable by the AI Agent.
    Every tool requires a valid DB session and an authenticated user_id.
    """

    def __init__(self, db: Session, user: models.User):
        self.db = db
        self.user = user
        self.user_id = user.user_id
        self.txn_repo = TransactionRepository(db)
        self.goal_repo = GoalRepository(db)
        self.user_repo = UserRepository(db)

    def get_transactions(self, limit: int = 20, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve recent transactions for the user (enforced 1-50)."""
        try:
            val = int(limit)
        except (ValueError, TypeError):
            val = 20
        safe_limit = max(1, min(50, val))
        txns = self.txn_repo.list_by_user(self.user_id, limit=safe_limit)
        return [
            {
                "transaction_id": t.transaction_id,
                "amount": float(t.amount or 0.0),
                "category": t.category or "other",
                "description": t.description or "",
                "date": t.date.strftime("%Y-%m-%d") if t.date else None,
                "payment_mode": getattr(t, "payment_mode", getattr(t, "source", "unknown"))
            }
            for t in txns
        ]

    def _extract_user_budget(self) -> float:
        if hasattr(self.user, "monthly_budget") and self.user.monthly_budget is not None:
            return float(self.user.monthly_budget)
        try:
            import json
            prefs = json.loads(self.user.preferences or "{}")
            if "monthly_budget" in prefs:
                return float(prefs["monthly_budget"])
        except Exception:
            pass
        return 0.0

    def get_budget(self, **kwargs) -> Dict[str, Any]:
        """Retrieve monthly budget and current month spend."""
        now = datetime.utcnow()
        start = datetime(now.year, now.month, 1)
        txns = self.txn_repo.get_in_date_range(self.user_id, start, now)
        total_spent = sum(t.amount for t in txns)
        monthly_budget = self._extract_user_budget()
        remaining = max(0.0, monthly_budget - total_spent) if monthly_budget > 0 else 0.0
        pct_used = round((total_spent / monthly_budget * 100.0) if monthly_budget > 0 else 0.0, 1)
        return {
            "monthly_budget": monthly_budget,
            "total_spent_this_month": round(total_spent, 2),
            "remaining_budget": round(remaining, 2),
            "utilization_pct": pct_used,
            "currency": self.user.currency,
            "currency_symbol": self.user.currency_symbol
        }

    def get_goals(self, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve active goals with pacing analysis."""
        goals = self.goal_repo.list_by_user(self.user_id)
        results = []
        for g in goals:
            eval_g = GoalPacingEngine.evaluate_goal(
                target_amount=g.target_amount,
                current_progress=g.current_progress or 0.0,
                deadline=g.deadline,
                created_at=g.created_at,
                goal_type=g.goal_type or "savings"
            )
            eval_g["goal_id"] = g.goal_id
            eval_g["goal_type"] = g.goal_type
            results.append(eval_g)
        return results

    def get_spending_summary(self, days: int = 30, **kwargs) -> Dict[str, Any]:
        """Get categorical spending summary for recent days (enforced 1-365 days)."""
        try:
            val = int(days)
        except (ValueError, TypeError):
            val = 30
        safe_days = max(1, min(365, val))
        start = datetime.utcnow() - timedelta(days=safe_days)
        txns = self.txn_repo.get_in_date_range(self.user_id, start, datetime.utcnow())
        return SpendingAnalytics.compute_spending_summary(txns)

    def get_anomalies(self, days: int = 60, **kwargs) -> List[Dict[str, Any]]:
        """Detect spending anomalies across rules, statistics, and ML (enforced 1-365 days)."""
        try:
            val = int(days)
        except (ValueError, TypeError):
            val = 60
        safe_days = max(1, min(365, val))
        start = datetime.utcnow() - timedelta(days=safe_days)
        txns = self.txn_repo.get_in_date_range(self.user_id, start, datetime.utcnow())
        profile = self.user_repo.get_profile(self.user_id)
        income = float(profile.monthly_income or 0.0) if profile else 0.0
        anomalies = LayeredAnomalyDetector.detect_anomalies(txns, monthly_income=income)
        return [
            {
                "transaction_id": a.transaction_id,
                "score": a.anomaly_score,
                "severity": a.severity,
                "reason": a.reason,
                "evidence": a.evidence
            }
            for a in anomalies
        ]

    def get_forecast(self, **kwargs) -> Dict[str, Any]:
        """Generate spending and cash flow forecast for 7, 30, and 90 days.
        Deterministic fixed 120-day history window; no arbitrary user-controlled limits."""
        start = datetime.utcnow() - timedelta(days=120)
        txns = self.txn_repo.get_in_date_range(self.user_id, start, datetime.utcnow())
        profile = self.user_repo.get_profile(self.user_id)
        income = float(profile.monthly_income or 0.0) if profile else 0.0
        return SpendingForecaster.generate_forecast(txns, monthly_income=income)

    def get_cashflow(self) -> Dict[str, Any]:
        """Generate 30-day cash flow projection and balance trajectory."""
        now = datetime.utcnow()
        start = datetime(now.year, now.month, 1)
        txns = self.txn_repo.get_in_date_range(self.user_id, start, now)
        profile = self.user_repo.get_profile(self.user_id)
        income = float(profile.monthly_income or 0.0) if profile else 0.0
        goals = self.goal_repo.list_by_user(self.user_id)
        subs = self.db.query(models.SubscriptionDecision).filter(
            models.SubscriptionDecision.user_id == self.user_id,
            models.SubscriptionDecision.action == "keep"
        ).all()
        return CashFlowEngine.calculate_cashflow(
            user=self.user,
            monthly_income=income,
            transactions=txns,
            goals=goals,
            initial_balance=float(self._extract_user_budget() or 1000.0),
            days_forward=30
        )

    def get_subscriptions(self) -> List[Dict[str, Any]]:
        """Detect recurring subscription charges."""
        start = datetime.utcnow() - timedelta(days=120)
        txns = self.txn_repo.get_in_date_range(self.user_id, start, datetime.utcnow())
        return SubscriptionIntelligenceEngine.detect_subscriptions(txns)

    def get_health_score(self) -> Dict[str, Any]:
        """Calculate explainable multi-factor financial health score."""
        start_30d = datetime.utcnow() - timedelta(days=30)
        txns_30d = self.txn_repo.get_in_date_range(self.user_id, start_30d, datetime.utcnow())
        total_spent = sum(t.amount for t in txns_30d)
        profile = self.user_repo.get_profile(self.user_id)
        income = float(profile.monthly_income or 0.0) if profile else 0.0
        budget_val = self._extract_user_budget()
        budget = budget_val if budget_val > 0 else None

        daily_map = {}
        for t in txns_30d:
            d_str = t.date.strftime("%Y-%m-%d")
            daily_map[d_str] = daily_map.get(d_str, 0.0) + t.amount
        daily_history = list(daily_map.values())

        goals = self.goal_repo.list_by_user(self.user_id)
        goal_statuses = [
            GoalPacingEngine.evaluate_goal(g.target_amount, g.current_progress or 0.0, g.deadline, g.created_at)["status"]
            for g in goals
        ]
        anomalies = LayeredAnomalyDetector.detect_anomalies(txns_30d, monthly_income=income)

        return ExplainableHealthScoreEngine.calculate(
            monthly_income=income,
            monthly_spending=total_spent,
            monthly_budget=budget,
            daily_spending_history=daily_history,
            goal_statuses=goal_statuses,
            anomaly_count=len(anomalies)
        )

    def dispatch(self, tool_name: str, **kwargs) -> Any:
        """Safe tool dispatcher."""
        allowed_tools = {
            "get_transactions": self.get_transactions,
            "get_budget": self.get_budget,
            "get_goals": self.get_goals,
            "get_spending_summary": self.get_spending_summary,
            "get_anomalies": self.get_anomalies,
            "get_forecast": self.get_forecast,
            "get_cashflow": self.get_cashflow,
            "get_subscriptions": self.get_subscriptions,
            "get_health_score": self.get_health_score,
        }
        if tool_name not in allowed_tools:
            return {"error": f"Tool '{tool_name}' is not permitted or unknown."}
        fn = allowed_tools[tool_name]
        return fn(**kwargs)
