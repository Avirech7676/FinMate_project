import pytest
from datetime import datetime, timedelta
from app.analytics.goals import GoalPacingEngine
from app.analytics.health_score import ExplainableHealthScoreEngine


def test_goal_pacing_completed():
    res = GoalPacingEngine.evaluate_goal(
        target_amount=1000.0,
        current_progress=1050.0,
        deadline=datetime.utcnow() + timedelta(days=60)
    )
    assert res["status"] == "COMPLETED"
    assert res["percent_completed"] == 100.0
    assert res["remaining_amount"] == 0.0


def test_goal_pacing_behind_past_deadline():
    past_deadline = datetime.utcnow() - timedelta(days=5)
    res = GoalPacingEngine.evaluate_goal(
        target_amount=1000.0,
        current_progress=300.0,
        deadline=past_deadline
    )
    assert res["status"] == "BEHIND"
    assert res["remaining_amount"] == 700.0


def test_goal_pacing_on_track():
    today = datetime(2026, 6, 1)
    created = datetime(2026, 4, 1) # 2 months ago
    deadline = datetime(2026, 8, 1) # 2 months ahead
    # target = 2000, current = 1000 (saved 500/mo, required 1000/2 = 500/mo)
    res = GoalPacingEngine.evaluate_goal(
        target_amount=2000.0,
        current_progress=1000.0,
        deadline=deadline,
        created_at=created,
        today=today
    )
    assert res["status"] == "ON_TRACK"
    assert res["remaining_amount"] == 1000.0
    assert res["required_monthly_contribution"] > 0


def test_explainable_health_score_excellent():
    score = ExplainableHealthScoreEngine.calculate(
        monthly_income=5000.0,
        monthly_spending=1500.0, # 30% spending -> 70% savings
        monthly_budget=2000.0,
        daily_spending_history=[50.0] * 30,
        goal_statuses=["ON_TRACK", "COMPLETED"],
        anomaly_count=0
    )
    assert score["overall_score"] >= 80
    assert score["label"] == "Excellent"
    assert "savings_surplus" in score["component_scores"]
    assert "budget_adherence" in score["component_scores"]
    assert "disclaimer" in score


def test_explainable_health_score_critical():
    score = ExplainableHealthScoreEngine.calculate(
        monthly_income=2000.0,
        monthly_spending=3500.0, # deep deficit
        monthly_budget=1800.0,
        daily_spending_history=[10.0, 500.0, 5.0, 1200.0, 20.0],
        goal_statuses=["BEHIND", "AT_RISK"],
        anomaly_count=3
    )
    assert score["overall_score"] < 50
    assert score["label"] in ["Needs Work", "Critical"]
    assert len(score["reasons_for_changes"]) > 0
