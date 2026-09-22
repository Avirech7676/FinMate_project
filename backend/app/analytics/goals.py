"""
FinMate 2.0 Goal Planning & Pacing Engine
Calculates deterministic goal progress, required contribution rate,
projected completion date, and risk status (ON_TRACK, AT_RISK, BEHIND, COMPLETED).
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import math


class GoalPacingEngine:
    @staticmethod
    def evaluate_goal(
        target_amount: float,
        current_progress: float,
        deadline: Optional[datetime],
        created_at: Optional[datetime] = None,
        goal_type: str = "savings",
        today: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Evaluate goal progress against timeline and required savings rate.
        """
        if today is None:
            today = datetime.utcnow()
        if created_at is None:
            created_at = today - timedelta(days=30)

        target = max(0.0, float(target_amount or 0.0))
        progress = max(0.0, float(current_progress or 0.0))
        remaining = max(0.0, round(target - progress, 2))
        pct_completed = round((progress / target * 100.0) if target > 0 else 100.0, 1)

        # If already completed
        if progress >= target and target > 0:
            return {
                "target_amount": target,
                "current_amount": progress,
                "remaining_amount": 0.0,
                "percent_completed": 100.0,
                "target_date": deadline.isoformat() if deadline else None,
                "days_remaining": 0,
                "required_monthly_contribution": 0.0,
                "required_daily_contribution": 0.0,
                "current_monthly_contribution_rate": round(progress, 2),
                "projected_completion_date": today.strftime("%Y-%m-%d"),
                "status": "COMPLETED",
                "explanation": f"Goal completed! Reached target of ₹{target:,.2f} with ₹{progress:,.2f} saved."
            }

        # Calculate time metrics
        days_elapsed = max(1, (today - created_at).days)
        months_elapsed = max(0.1, days_elapsed / 30.4375)
        current_monthly_rate = round(progress / months_elapsed, 2)

        days_remaining = None
        required_monthly = 0.0
        required_daily = 0.0
        projected_completion_str = None
        status = "ON_TRACK"

        if deadline:
            time_left = deadline - today
            days_remaining = time_left.days

            if days_remaining <= 0:
                # Deadline passed and not completed
                status = "BEHIND"
                required_monthly = remaining
                required_daily = remaining
                explanation = (
                    f"Deadline passed on {deadline.strftime('%Y-%m-%d')}. "
                    f"Remaining shortfall is ₹{remaining:,.2f}."
                )
            else:
                months_remaining = max(0.1, days_remaining / 30.4375)
                required_monthly = round(remaining / months_remaining, 2)
                required_daily = round(remaining / days_remaining, 2)

                # Status determination based on required rate vs current rate
                if current_monthly_rate >= required_monthly * 0.95:
                    status = "ON_TRACK"
                    explanation = (
                        f"On track: Saving ₹{current_monthly_rate:,.2f}/mo vs required "
                        f"₹{required_monthly:,.2f}/mo ({pct_completed}% complete)."
                    )
                elif current_monthly_rate >= required_monthly * 0.65:
                    status = "AT_RISK"
                    explanation = (
                        f"At risk: Saving ₹{current_monthly_rate:,.2f}/mo, which is below "
                        f"the required ₹{required_monthly:,.2f}/mo to finish by {deadline.strftime('%Y-%m-%d')}."
                    )
                else:
                    status = "BEHIND"
                    explanation = (
                        f"Behind schedule: Saving ₹{current_monthly_rate:,.2f}/mo against required "
                        f"₹{required_monthly:,.2f}/mo shortfall of ₹{remaining:,.2f}."
                    )
        else:
            # No deadline set, determine completion date based on current rate
            explanation = f"Saved ₹{progress:,.2f} of ₹{target:,.2f} ({pct_completed}% complete). No deadline specified."

        # Project completion date if saving at current monthly rate
        if current_monthly_rate > 0 and remaining > 0:
            months_needed = remaining / current_monthly_rate
            days_needed = int(months_needed * 30.4375)
            projected_completion = today + timedelta(days=days_needed)
            projected_completion_str = projected_completion.strftime("%Y-%m-%d")
        elif remaining == 0:
            projected_completion_str = today.strftime("%Y-%m-%d")

        return {
            "target_amount": target,
            "current_amount": progress,
            "remaining_amount": remaining,
            "percent_completed": min(100.0, pct_completed),
            "target_date": deadline.isoformat() if deadline else None,
            "days_remaining": days_remaining,
            "required_monthly_contribution": required_monthly,
            "required_daily_contribution": required_daily,
            "current_monthly_contribution_rate": current_monthly_rate,
            "projected_completion_date": projected_completion_str,
            "status": status,
            "explanation": explanation
        }
