from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import models

@dataclass
class RuleEvaluationResult:
    rule_id: str
    rule_name: str
    triggered: bool
    severity: str  # "info", "warning", "critical"
    message: str
    evidence: Dict[str, Any]

class FinancialRuleEngine:
    """
    Deterministic rule engine that evaluates financial constraints and anomalies.
    Does NOT use LLM for calculation; produces structured verifiable evidence.
    """

    @staticmethod
    def evaluate_all(
        user: models.User,
        current_month_spending: float,
        monthly_income: float,
        goals: List[models.BudgetGoal],
        recent_transactions: List[models.Transaction]
    ) -> List[RuleEvaluationResult]:
        results: List[RuleEvaluationResult] = []

        # Rule 1: Cash-Flow Shortage (Spending exceeds income)
        if monthly_income > 0:
            burn_ratio = current_month_spending / monthly_income
            if burn_ratio > 1.0:
                results.append(RuleEvaluationResult(
                    rule_id="RULE_CASHFLOW_DEFICIT",
                    rule_name="Cash-Flow Deficit",
                    triggered=True,
                    severity="critical",
                    message=f"Current monthly spending ({current_month_spending:.2f}) exceeds monthly income ({monthly_income:.2f}).",
                    evidence={
                        "monthly_income": monthly_income,
                        "current_spending": current_month_spending,
                        "deficit": round(current_month_spending - monthly_income, 2),
                        "burn_ratio": round(burn_ratio, 2)
                    }
                ))
            elif burn_ratio > 0.85:
                results.append(RuleEvaluationResult(
                    rule_id="RULE_CASHFLOW_TIGHT",
                    rule_name="High Burn Rate",
                    triggered=True,
                    severity="warning",
                    message=f"You have utilized {burn_ratio * 100:.1f}% of your monthly income.",
                    evidence={
                        "monthly_income": monthly_income,
                        "current_spending": current_month_spending,
                        "burn_ratio": round(burn_ratio, 2)
                    }
                ))

        # Rule 2: Goal at risk
        now = datetime.utcnow()
        for g in goals:
            if g.status == "active" and g.deadline and g.target_amount > 0:
                days_left = (g.deadline - now).days
                remaining_amt = max(0.0, g.target_amount - (g.current_progress or 0.0))
                if days_left <= 14 and remaining_amt > 0.3 * g.target_amount:
                    results.append(RuleEvaluationResult(
                        rule_id=f"RULE_GOAL_AT_RISK_{g.goal_id}",
                        rule_name="Goal Behind Schedule",
                        triggered=True,
                        severity="warning",
                        message=f"Goal '{g.goal_type}' requires {remaining_amt:.2f} within {days_left} days.",
                        evidence={
                            "goal_id": g.goal_id,
                            "goal_type": g.goal_type,
                            "target_amount": g.target_amount,
                            "current_progress": g.current_progress,
                            "remaining_amount": remaining_amt,
                            "days_remaining": days_left
                        }
                    ))

        # Rule 3: Large Transaction Outlier (>30% of monthly income or >$500 single transaction)
        if recent_transactions:
            for t in recent_transactions[:10]:
                amt = float(t.amount or 0.0)
                threshold = max(500.0, monthly_income * 0.25 if monthly_income > 0 else 500.0)
                if amt >= threshold:
                    results.append(RuleEvaluationResult(
                        rule_id=f"RULE_HIGH_EXPENSE_{t.transaction_id}",
                        rule_name="Unusual High-Value Expense",
                        triggered=True,
                        severity="info",
                        message=f"High-value purchase of {amt:.2f} detected at '{t.description}'.",
                        evidence={
                            "transaction_id": t.transaction_id,
                            "amount": amt,
                            "category": t.category,
                            "description": t.description,
                            "threshold": threshold
                        }
                    ))

        return results
