"""
FinMate 2.0 Downloadable Financial Report Service
Assembles clean, multi-section financial reports covering Overview, Income, Expenses,
Budgets, Goals, Anomalies, Forecasts, and Health Scores.
Sanitized: Never exposes API keys, tokens, or private secrets.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

import models
from app.analytics.spending import SpendingAnalytics
from app.analytics.briefing import WeeklyBriefingEngine
from app.analytics.health_score import ExplainableHealthScoreEngine
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.user_repo import UserRepository
from app.repositories.goal_repo import GoalRepository


class FinancialReportService:
    @staticmethod
    def generate_report_data(db: Session, user: models.User) -> Dict[str, Any]:
        now = datetime.utcnow()
        txn_repo = TransactionRepository(db)
        user_repo = UserRepository(db)
        goal_repo = GoalRepository(db)

        start_30d = now - timedelta(days=30)
        txns = txn_repo.get_in_date_range(user.user_id, start_30d, now)
        profile = user_repo.get_profile(user.user_id)
        income = float(profile.monthly_income or 0.0) if profile else 0.0
        budget = float(user.monthly_budget or 0.0) if hasattr(user, "monthly_budget") and user.monthly_budget else 0.0

        spending_summary = SpendingAnalytics.compute_spending_summary(txns)
        briefing = WeeklyBriefingEngine.generate_briefing(db, user)

        # Health score
        daily_map = {}
        for t in txns:
            d_str = t.date.strftime("%Y-%m-%d") if t.date else "unknown"
            daily_map[d_str] = daily_map.get(d_str, 0.0) + t.amount

        goals = goal_repo.list_by_user(user.user_id)
        health_score = ExplainableHealthScoreEngine.calculate(
            monthly_income=income,
            monthly_spending=spending_summary.get("total_spent", 0.0),
            monthly_budget=budget if budget > 0 else None,
            daily_spending_history=list(daily_map.values()),
            goal_statuses=[g.get("status") for g in briefing.get("goal_progress", [])]
        )

        return {
            "title": f"FinMate 2.0 Financial Intelligence Report — {now.strftime('%B %Y')}",
            "generated_at": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "user": {
                "name": user.full_name or "Valued Client",
                "email": user.email,
                "currency": user.currency,
                "currency_symbol": user.currency_symbol or "$"
            },
            "overview": {
                "monthly_income": income,
                "monthly_spending_30d": spending_summary.get("total_spent", 0.0),
                "monthly_budget": budget,
                "net_savings": round(income - spending_summary.get("total_spent", 0.0), 2)
            },
            "health_score": health_score,
            "spending_categories": spending_summary.get("by_category", {}),
            "weekly_briefing": briefing,
            "goals": briefing.get("goal_progress", []),
            "anomalies": briefing.get("unusual_transactions", []),
            "disclaimer": (
                "CONFIDENTIAL & PRIVILEGED: This document contains personal financial analytics "
                "generated automatically by FinMate 2.0. This report is for personal educational "
                "purposes only and does not constitute certified accounting, tax, or investment advisory."
            )
        }

    @classmethod
    def generate_html_report(cls, db: Session, user: models.User) -> str:
        """
        Produces clean, printable HTML document suitable for browser printing or saving as PDF.
        """
        data = cls.generate_report_data(db, user)
        curr = data["user"]["currency_symbol"]

        cat_rows = "".join(
            f"<tr><td style='padding:8px;border-bottom:1px solid #ddd;'>{cat.title()}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #ddd;text-align:right;'>{curr}{amt:,.2f}</td></tr>"
            for cat, amt in data["spending_categories"].items()
        ) or "<tr><td colspan='2' style='padding:8px;'>No spending recorded</td></tr>"

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{data['title']}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; color: #111; line-height: 1.5; }}
  .header {{ border-bottom: 2px solid #0891b2; padding-bottom: 16px; margin-bottom: 24px; }}
  .title {{ font-size: 24px; font-weight: bold; color: #0891b2; }}
  .meta {{ font-size: 12px; color: #666; margin-top: 4px; }}
  .grid {{ display: flex; gap: 20px; margin-bottom: 24px; }}
  .card {{ flex: 1; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; background: #f9fafb; }}
  .card-title {{ font-size: 11px; text-transform: uppercase; color: #6b7280; font-weight: 600; }}
  .card-val {{ font-size: 20px; font-weight: bold; margin-top: 4px; }}
  h3 {{ font-size: 16px; margin-top: 24px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 8px; }}
  .disclaimer {{ font-size: 11px; color: #9ca3af; margin-top: 40px; border-top: 1px solid #e5e7eb; padding-top: 12px; }}
  @media print {{ body {{ margin: 0; }} }}
</style>
</head>
<body>
  <div class="header">
    <div class="title">FinMate 2.0 Financial Intelligence Report</div>
    <div class="meta">Prepared for: {data['user']['name']} ({data['user']['email']}) | Generated: {data['generated_at']}</div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="card-title">Monthly Income</div>
      <div class="card-val">{curr}{data['overview']['monthly_income']:,.2f}</div>
    </div>
    <div class="card">
      <div class="card-title">30-Day Spending</div>
      <div class="card-val">{curr}{data['overview']['monthly_spending_30d']:,.2f}</div>
    </div>
    <div class="card">
      <div class="card-title">Net Surplus</div>
      <div class="card-val">{curr}{data['overview']['net_savings']:,.2f}</div>
    </div>
    <div class="card">
      <div class="card-title">Health Score</div>
      <div class="card-val">{data['health_score']['overall_score']}/100 ({data['health_score']['label']})</div>
    </div>
  </div>

  <h3>Category Spending Breakdown</h3>
  <table>
    <thead>
      <tr style="background:#f3f4f6;">
        <th style="padding:8px;text-align:left;">Category</th>
        <th style="padding:8px;text-align:right;">Amount</th>
      </tr>
    </thead>
    <tbody>
      {cat_rows}
    </tbody>
  </table>

  <h3>Actionable Weekly Suggestions</h3>
  <ul>
    {"".join(f"<li>{s}</li>" for s in data['weekly_briefing'].get('actionable_suggestions', []))}
  </ul>

  <div class="disclaimer">
    {data['disclaimer']}
  </div>
</body>
</html>"""
