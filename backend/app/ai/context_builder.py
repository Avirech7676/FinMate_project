"""
FinMate 2.0 AI Context Builder
Constructs compact, scoped, token-efficient user financial summaries for LLM inference.
Ensures zero data leakage across users and limits context size.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models
from app.ai.tool_registry import ToolRegistry
from app.ai.guardrails import AIGuardrails


class AIContextBuilder:
    """
    Builds a structured, compact JSON representation of the authenticated user's financial status.
    """

    @staticmethod
    def build_compact_context(
        db: Session,
        user: models.User,
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        tools = ToolRegistry(db, user)

        # Baseline vital stats
        budget_info = tools.get_budget()
        spending_summary = tools.get_spending_summary(days=30)
        recent_txns = tools.get_transactions(limit=10)
        goals = tools.get_goals()[:5]

        context: Dict[str, Any] = {
            "user_id": user.user_id,
            "currency": user.currency,
            "currency_symbol": user.currency_symbol,
            "budget": budget_info,
            "spending_30d": {
                "total_spent": spending_summary.get("total_spent", 0.0),
                "top_categories": spending_summary.get("by_category", {})
            },
            "recent_transactions": [
                {
                    "transaction_id": t.get("transaction_id"),
                    "amount": t.get("amount"),
                    "category": t.get("category"),
                    "description": AIGuardrails.sanitize_field(t.get("description", "")),
                    "date": t.get("date")
                }
                for t in recent_txns
            ],
            "goals": [
                {
                    "goal_id": g.get("goal_id"),
                    "target_amount": g.get("target_amount"),
                    "current_amount": g.get("current_amount"),
                    "status": g.get("status"),
                    "explanation": g.get("explanation")
                }
                for g in goals
            ]
        }

        # Query-specific enrichments
        q_lower = (user_query or "").lower()
        if any(w in q_lower for w in ["anomaly", "unusual", "suspicious", "fraud", "spike"]):
            context["anomalies"] = tools.get_anomalies(days=45)[:5]

        if any(w in q_lower for w in ["forecast", "future", "predict", "next month", "ahead"]):
            forecast = tools.get_forecast()
            context["forecast"] = {
                "30d_projected_spending": forecast.get("30d", {}).get("projected_spending"),
                "trend_direction": forecast.get("trend_direction"),
                "assumptions": forecast.get("assumptions")
            }

        if any(w in q_lower for w in ["cashflow", "runway", "burn", "balance", "shortage"]):
            cf = tools.get_cashflow()
            context["cashflow"] = {
                "risk_status": cf.get("risk_status"),
                "risk_reason": cf.get("risk_reason"),
                "projected_end_balance": cf.get("projected_end_balance"),
                "net_cash_flow": cf.get("metrics", {}).get("net_cash_flow")
            }

        if any(w in q_lower for w in ["subscription", "recurring", "monthly charge", "netflix", "spotify"]):
            context["subscriptions"] = tools.get_subscriptions()[:6]

        if any(w in q_lower for w in ["health", "score", "rate my", "how am i doing"]):
            hs = tools.get_health_score()
            context["health_score"] = {
                "overall_score": hs.get("overall_score"),
                "label": hs.get("label"),
                "reasons": hs.get("reasons_for_changes", [])[:3]
            }

        return context
