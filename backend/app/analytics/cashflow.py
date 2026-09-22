from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import models
from app.analytics.subscriptions import SubscriptionIntelligenceEngine, SubscriptionCandidate

class CashFlowEngine:
    """
    Deterministic Cash-Flow Projection Engine.
    Calculates fixed vs variable expenses, recurring obligations, goal pacing,
    and forwards 30-day balance trajectories.
    """

    @classmethod
    def calculate_cashflow(
        cls,
        user: models.User,
        monthly_income: float,
        transactions: List[models.Transaction],
        goals: List[models.BudgetGoal],
        initial_balance: float = 0.0,
        days_forward: int = 30
    ) -> Dict[str, Any]:
        # Detect active subscriptions
        subscriptions = SubscriptionIntelligenceEngine.detect_subscriptions(transactions, user.user_id)

        # Monthly recurring cost from subscriptions
        monthly_recurring = sum(s.annualized_cost / 12.0 for s in subscriptions if s.confidence >= 0.4)

        # Separate fixed vs variable historical expenses
        fixed_categories = {"housing", "utilities", "bills", "rent", "insurance"}
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        recent_txns = [t for t in transactions if t.date and t.date >= thirty_days_ago and t.amount and t.amount > 0]

        fixed_spent = 0.0
        variable_spent = 0.0

        for t in recent_txns:
            amt = float(t.amount)
            cat = (t.category or "").lower()
            if cat in fixed_categories:
                fixed_spent += amt
            else:
                variable_spent += amt

        # Goal periodic contributions needed (monthly)
        monthly_goal_target = 0.0
        for g in goals:
            if g.status == "active" and g.deadline and g.target_amount > 0:
                rem_amt = max(0.0, float(g.target_amount) - float(g.current_progress or 0.0))
                days_left = max(1, (g.deadline - now).days)
                monthly_share = (rem_amt / days_left) * 30.0
                monthly_goal_target += monthly_share

        total_current_expenses = fixed_spent + variable_spent
        current_cash_flow = round(monthly_income - total_current_expenses, 2)

        # Projected expenses for upcoming 30 days
        # Use recurring subscriptions + recent variable velocity
        projected_fixed = round(max(fixed_spent, monthly_recurring), 2)
        projected_variable = round(variable_spent, 2)
        projected_goals = round(monthly_goal_target, 2)
        projected_total_expenses = round(projected_fixed + projected_variable + projected_goals, 2)
        projected_cash_flow = round(monthly_income - projected_total_expenses, 2)

        # Cash flow risk evaluation
        if monthly_income <= 0:
            risk = "high" if total_current_expenses > 0 else "low"
        elif projected_cash_flow < 0:
            risk = "critical" if abs(projected_cash_flow) > 0.2 * monthly_income else "high"
        elif projected_cash_flow < (0.1 * monthly_income):
            risk = "moderate"
        else:
            risk = "low"

        # Trajectory simulation over next days_forward days
        daily_income_rate = monthly_income / 30.0
        daily_expense_rate = (projected_fixed + projected_variable) / 30.0
        daily_goal_rate = projected_goals / 30.0

        balance_timeline = []
        running_balance = initial_balance
        for d in range(1, days_forward + 1):
            future_day = now + timedelta(days=d)
            # Add pro-rated income and subtract daily run-rate
            running_balance += (daily_income_rate - daily_expense_rate - daily_goal_rate)
            balance_timeline.append({
                "day": d,
                "date": future_day.strftime("%Y-%m-%d"),
                "projected_balance": round(running_balance, 2)
            })

        return {
            "monthly_income": round(monthly_income, 2),
            "current_monthly_expenses": {
                "total": round(total_current_expenses, 2),
                "fixed": round(fixed_spent, 2),
                "variable": round(variable_spent, 2),
                "recurring_subscriptions": round(monthly_recurring, 2)
            },
            "projected_30_day_expenses": {
                "total": projected_total_expenses,
                "fixed_obligations": projected_fixed,
                "variable_spending": projected_variable,
                "goal_contributions": projected_goals
            },
            "current_cash_flow": current_cash_flow,
            "projected_cash_flow": projected_cash_flow,
            "cash_flow_risk": risk,
            "detected_subscriptions_count": len(subscriptions),
            "balance_projection_30d": balance_timeline
        }
