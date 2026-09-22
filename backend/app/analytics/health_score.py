"""
FinMate 2.0 Explainable Financial Health Score Engine
Calculates multi-dimensional financial health score with weighted component breakdown,
clear numerical explanations, key positive/negative drivers, and legal disclaimers.
"""

from typing import Dict, Any, List, Optional
import statistics


class ExplainableHealthScoreEngine:
    """
    Computes an explainable 0-100 financial health score across 5 key dimensions:
    1. Savings & Surplus (25%)
    2. Budget Adherence (25%)
    3. Cash Flow Health (20%)
    4. Goal Progress & Pacing (15%)
    5. Spending Consistency (15%)
    """

    WEIGHTS = {
        "savings_surplus": 0.25,
        "budget_adherence": 0.25,
        "cash_flow_health": 0.20,
        "goal_progress": 0.15,
        "spending_consistency": 0.15,
    }

    DISCLAIMER = (
        "This financial health score is an algorithmic educational assessment based on your "
        "tracked transactions, budgets, and goals. It does not constitute professional financial, "
        "legal, or tax advice, nor is it a credit score or financial certification."
    )

    @classmethod
    def calculate(
        cls,
        monthly_income: Optional[float],
        monthly_spending: float,
        monthly_budget: Optional[float] = None,
        daily_spending_history: Optional[List[float]] = None,
        goal_statuses: Optional[List[str]] = None,
        anomaly_count: int = 0
    ) -> Dict[str, Any]:
        income = float(monthly_income or 0.0)
        spending = max(0.0, float(monthly_spending or 0.0))
        budget = float(monthly_budget or 0.0) if monthly_budget else None
        daily_spending = daily_spending_history or []
        goals = goal_statuses or []

        reasons: List[str] = []

        # 1. Savings & Surplus (25%)
        savings_score = 50.0
        if income > 0:
            savings_rate = (income - spending) / income
            if savings_rate >= 0.30:
                savings_score = 100.0
                reasons.append(f"Strong savings rate of {savings_rate * 100:.1f}% (+25 pts)")
            elif savings_rate >= 0.20:
                savings_score = 85.0
                reasons.append(f"Healthy savings rate of {savings_rate * 100:.1f}% (+21 pts)")
            elif savings_rate >= 0.10:
                savings_score = 70.0
                reasons.append(f"Moderate savings rate of {savings_rate * 100:.1f}% (+17.5 pts)")
            elif savings_rate >= 0.0:
                savings_score = 50.0
                reasons.append(f"Thin surplus margin of {savings_rate * 100:.1f}% (+12.5 pts)")
            else:
                deficit_pct = abs(savings_rate) * 100
                savings_score = max(10.0, 50.0 - deficit_pct * 0.8)
                reasons.append(f"Spending exceeds income by {deficit_pct:.1f}% (-warning)")
        else:
            # Baseline when income is unrecorded
            if spending < 1500:
                savings_score = 75.0
            elif spending < 3500:
                savings_score = 60.0
            else:
                savings_score = 40.0
            reasons.append("Income not specified; baseline benchmark applied based on spend magnitude.")

        # 2. Budget Adherence (25%)
        budget_score = 70.0
        if budget and budget > 0:
            utilization = spending / budget
            if utilization <= 0.80:
                budget_score = 100.0
                reasons.append(f"Under monthly budget at {utilization * 100:.1f}% utilization.")
            elif utilization <= 1.00:
                budget_score = 85.0
                reasons.append(f"Within monthly budget limits at {utilization * 100:.1f}% utilization.")
            elif utilization <= 1.15:
                budget_score = 55.0
                reasons.append(f"Mild budget overrun of {(utilization - 1.0) * 100:.1f}%.")
            else:
                budget_score = max(15.0, 100.0 - utilization * 60.0)
                reasons.append(f"High budget overrun of {(utilization - 1.0) * 100:.1f}%.")
        else:
            # No budget configured: neutral score
            budget_score = 65.0
            reasons.append("No active monthly budget ceiling set; recommend creating a budget.")

        # 3. Cash Flow Health (20%)
        net_cashflow = (income - spending) if income > 0 else -spending
        if income > 0 and net_cashflow > 0:
            cashflow_ratio = net_cashflow / income
            cashflow_score = min(100.0, 60.0 + cashflow_ratio * 100.0)
        elif income > 0 and net_cashflow <= 0:
            cashflow_score = max(15.0, 50.0 - (abs(net_cashflow) / income) * 80.0)
        else:
            cashflow_score = 60.0 if spending < 2000 else 40.0

        # 4. Goal Progress & Pacing (15%)
        if goals:
            completed_or_on_track = sum(1 for g in goals if g.upper() in ["COMPLETED", "ON_TRACK"])
            at_risk = sum(1 for g in goals if g.upper() == "AT_RISK")
            goal_score = (completed_or_on_track * 100.0 + at_risk * 50.0) / len(goals)
            reasons.append(f"{completed_or_on_track}/{len(goals)} financial goals on track or completed.")
        else:
            goal_score = 60.0  # Neutral baseline
            reasons.append("No financial goals tracked; adding targets improves score.")

        # 5. Spending Consistency (15%)
        if len(daily_spending) >= 5:
            mean_spend = statistics.mean(daily_spending)
            stdev = statistics.stdev(daily_spending)
            cv = (stdev / mean_spend) if mean_spend > 0 else 0.0
            if cv < 0.6:
                consistency_score = 95.0
            elif cv < 1.0:
                consistency_score = 80.0
            elif cv < 1.5:
                consistency_score = 65.0
            else:
                consistency_score = 45.0
        else:
            consistency_score = 75.0

        # Anomaly penalty
        if anomaly_count > 0:
            consistency_score = max(10.0, consistency_score - min(30.0, anomaly_count * 10.0))
            reasons.append(f"{anomaly_count} spending anomalies detected in recent history.")

        # Aggregate weighted score
        overall = (
            savings_score * cls.WEIGHTS["savings_surplus"] +
            budget_score * cls.WEIGHTS["budget_adherence"] +
            cashflow_score * cls.WEIGHTS["cash_flow_health"] +
            goal_score * cls.WEIGHTS["goal_progress"] +
            consistency_score * cls.WEIGHTS["spending_consistency"]
        )
        overall_score = int(round(max(0.0, min(100.0, overall))))

        # Rating label & color
        if overall_score >= 80:
            label = "Excellent"
            color = "#10b981"
        elif overall_score >= 65:
            label = "Good"
            color = "#3b82f6"
        elif overall_score >= 50:
            label = "Fair"
            color = "#f59e0b"
        elif overall_score >= 35:
            label = "Needs Work"
            color = "#f97316"
        else:
            label = "Critical"
            color = "#ef4444"

        components = {
            "savings_surplus": {
                "score": round(savings_score, 1),
                "weight": cls.WEIGHTS["savings_surplus"],
                "weighted_score": round(savings_score * cls.WEIGHTS["savings_surplus"], 1),
                "rating": "Healthy" if savings_score >= 70 else "At Risk",
                "description": "Portion of total income retained after living expenditures."
            },
            "budget_adherence": {
                "score": round(budget_score, 1),
                "weight": cls.WEIGHTS["budget_adherence"],
                "weighted_score": round(budget_score * cls.WEIGHTS["budget_adherence"], 1),
                "rating": "On Track" if budget_score >= 70 else "Over Limit",
                "description": "Discipline in staying within allocated monthly category limits."
            },
            "cash_flow_health": {
                "score": round(cashflow_score, 1),
                "weight": cls.WEIGHTS["cash_flow_health"],
                "weighted_score": round(cashflow_score * cls.WEIGHTS["cash_flow_health"], 1),
                "rating": "Positive" if cashflow_score >= 65 else "Tight",
                "description": "Net monthly liquidity surplus preventing cash shortages."
            },
            "goal_progress": {
                "score": round(goal_score, 1),
                "weight": cls.WEIGHTS["goal_progress"],
                "weighted_score": round(goal_score * cls.WEIGHTS["goal_progress"], 1),
                "rating": "Good Progress" if goal_score >= 70 else "Falling Behind",
                "description": "Progress and pace on active savings, debt, or investment goals."
            },
            "spending_consistency": {
                "score": round(consistency_score, 1),
                "weight": cls.WEIGHTS["spending_consistency"],
                "weighted_score": round(consistency_score * cls.WEIGHTS["spending_consistency"], 1),
                "rating": "Stable" if consistency_score >= 70 else "Volatile",
                "description": "Consistency in daily expense patterns and absence of irregular spikes."
            }
        }

        return {
            "overall_score": overall_score,
            "label": label,
            "color": color,
            "component_scores": components,
            "reasons_for_changes": reasons[:5],
            "disclaimer": cls.DISCLAIMER
        }
