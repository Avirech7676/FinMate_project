"""
FinMate 2.0 Financial What-If Simulator Service
Computes deterministic multi-factor impacts of hypothetical purchases on monthly budget,
active financial goals, and projected cash flow trajectories.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

import models
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.goal_repo import GoalRepository
from app.repositories.user_repo import UserRepository
from app.analytics.spending import SpendingAnalytics
from app.analytics.cashflow import CashFlowEngine
from app.analytics.goals import GoalPacingEngine


class FinancialSimulatorService:
    def __init__(self, db: Session):
        self.db = db
        self.txn_repo = TransactionRepository(db)
        self.goal_repo = GoalRepository(db)
        self.user_repo = UserRepository(db)

    def _get_user_budget(self, user: models.User) -> float:
        if hasattr(user, "monthly_budget") and user.monthly_budget is not None:
            return float(user.monthly_budget)
        try:
            prefs = json.loads(user.preferences or "{}")
            if "monthly_budget" in prefs:
                return float(prefs["monthly_budget"])
        except Exception:
            pass
        return 0.0

    def simulate_purchase(
        self,
        user: models.User,
        purchase_amount: float,
        purchase_category: str = "shopping",
        purchase_date: Optional[datetime] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates exact deterministic impacts of an intended purchase.
        """
        now = purchase_date or datetime.utcnow()
        amount = max(0.01, float(purchase_amount))
        category = (purchase_category or "shopping").lower()

        # 1. Month-to-date spending
        start_m = datetime(now.year, now.month, 1)
        month_txns = self.txn_repo.get_in_date_range(user.user_id, start_m, now)
        current_spent = sum(t.amount for t in month_txns)
        monthly_budget = self._get_user_budget(user)

        # Profile income
        profile = self.user_repo.get_profile(user.user_id)
        monthly_income = float(profile.monthly_income or 0.0) if profile else 0.0

        # Category spending so far
        cat_spent_so_far = sum(t.amount for t in month_txns if (t.category or "").lower() == category)

        # Post-purchase values
        post_spent = round(current_spent + amount, 2)
        post_cat_spent = round(cat_spent_so_far + amount, 2)

        # 2. Budget Impact
        budget_status = "WITHIN_BUDGET"
        budget_delta_pct = 0.0
        current_utilization = round((current_spent / monthly_budget * 100.0) if monthly_budget > 0 else 0.0, 1)
        post_utilization = round((post_spent / monthly_budget * 100.0) if monthly_budget > 0 else 0.0, 1)

        if monthly_budget > 0:
            if post_spent > monthly_budget:
                budget_status = "EXCEEDS_BUDGET"
            elif post_utilization >= 85.0:
                budget_status = "NEAR_LIMIT"
            budget_delta_pct = round(post_utilization - current_utilization, 1)

        budget_impact = {
            "monthly_budget": monthly_budget,
            "current_spent": round(current_spent, 2),
            "post_purchase_spent": post_spent,
            "current_utilization_pct": current_utilization,
            "post_utilization_pct": post_utilization,
            "utilization_delta_pct": budget_delta_pct,
            "category": category,
            "current_category_spent": round(cat_spent_so_far, 2),
            "post_category_spent": post_cat_spent,
            "status": budget_status
        }

        # 3. Cash Flow Impact
        active_subs = self.db.query(models.SubscriptionDecision).filter(
            models.SubscriptionDecision.user_id == user.user_id,
            models.SubscriptionDecision.action == "keep"
        ).all()
        user_goals = self.goal_repo.list_by_user(user.user_id)

        baseline_balance = float(monthly_income if monthly_income > 0 else (monthly_budget or 2000.0))
        cf_baseline = CashFlowEngine.calculate_cashflow(
            user=user,
            monthly_income=monthly_income,
            transactions=month_txns,
            goals=user_goals,
            initial_balance=baseline_balance,
            days_forward=30
        )

        post_balance = round(baseline_balance - amount, 2)
        cf_post = CashFlowEngine.calculate_cashflow(
            user=user,
            monthly_income=monthly_income,
            transactions=month_txns,
            goals=user_goals,
            initial_balance=post_balance,
            days_forward=30
        )

        base_end = cf_baseline["balance_projection_30d"][-1]["projected_balance"] if cf_baseline["balance_projection_30d"] else baseline_balance
        post_end = cf_post["balance_projection_30d"][-1]["projected_balance"] if cf_post["balance_projection_30d"] else post_balance

        cash_flow_impact = {
            "current_projected_end_balance": base_end,
            "post_purchase_projected_end_balance": post_end,
            "balance_delta": -amount,
            "current_risk_status": cf_baseline["cash_flow_risk"],
            "post_purchase_risk_status": cf_post["cash_flow_risk"]
        }

        # 4. Goal Impact
        goal_impacts = []
        for g in user_goals:
            pacing_before = GoalPacingEngine.evaluate_goal(
                g.target_amount, g.current_progress or 0.0, g.deadline, g.created_at
            )
            # If savings balance is depleted, assess if goal contribution could be crowded out
            pacing_after = pacing_before.copy()
            if cf_post["cash_flow_risk"] in ["high", "critical"]:
                pacing_after["status"] = "AT_RISK"
                pacing_after["explanation"] = (
                    f"Cash-flow tightening from this ₹{amount:,.2f} purchase puts "
                    f"this goal at risk of reduced monthly contributions."
                )

            goal_impacts.append({
                "goal_id": g.goal_id,
                "goal_type": g.goal_type,
                "target_amount": g.target_amount,
                "current_progress": g.current_progress,
                "status_before": pacing_before["status"],
                "status_after": pacing_after["status"],
                "is_delayed": pacing_before["status"] == "ON_TRACK" and pacing_after["status"] != "ON_TRACK"
            })

        # 5. Overall Verdict & Recommendation
        if budget_status == "EXCEEDS_BUDGET" or cf_post["cash_flow_risk"] == "critical":
            verdict = "UNRECOMMENDED"
            risk_level = "HIGH"
            overrun = post_spent - monthly_budget if monthly_budget > 0 else amount
            recommendation = (
                f"Purchase of ₹{amount:,.2f} will exceed your monthly budget by "
                f"₹{overrun:,.2f} ({post_utilization}% utilization). Delaying or reducing "
                f"this discretionary expense is strongly advised."
            )
        elif budget_status == "NEAR_LIMIT" or cf_post["cash_flow_risk"] in ["moderate", "high"]:
            verdict = "PROCEED_WITH_CAUTION"
            risk_level = "MODERATE"
            recommendation = (
                f"Purchase of ₹{amount:,.2f} increases budget utilization to {post_utilization}%. "
                f"Ensure no additional large purchases occur this billing cycle."
            )
        else:
            verdict = "AFFORDABLE"
            risk_level = "LOW"
            recommendation = (
                f"Purchase of ₹{amount:,.2f} is well within budget limits ({post_utilization}% utilization) "
                f"and preserves a safe cash flow runway."
            )

        return {
            "simulation_id": f"sim_{int(now.timestamp())}",
            "purchase_amount": amount,
            "purchase_category": category,
            "description": description or f"Simulated {category} purchase",
            "verdict": verdict,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "budget_impact": budget_impact,
            "cash_flow_impact": cash_flow_impact,
            "goal_impacts": goal_impacts
        }
