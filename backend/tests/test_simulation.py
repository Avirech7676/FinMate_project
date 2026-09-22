import pytest
from datetime import datetime, timedelta
from app.services.simulation_service import FinancialSimulatorService
import models


def test_simulation_affordable_purchase(db_session, test_user):
    svc = FinancialSimulatorService(db_session)
    res = svc.simulate_purchase(
        user=test_user,
        purchase_amount=50.0,
        purchase_category="groceries"
    )
    assert res["verdict"] == "AFFORDABLE"
    assert res["risk_level"] == "LOW"
    assert "budget_impact" in res
    assert "cash_flow_impact" in res
    assert "goal_impacts" in res
    assert res["budget_impact"]["post_purchase_spent"] >= 50.0


def test_simulation_unrecommended_purchase(db_session, test_user):
    # Test user has budget = 2500. Simulate a huge purchase of 10000
    svc = FinancialSimulatorService(db_session)
    res = svc.simulate_purchase(
        user=test_user,
        purchase_amount=10000.0,
        purchase_category="electronics",
        description="Luxury VR Headset & Rig"
    )
    assert res["verdict"] == "UNRECOMMENDED"
    assert res["risk_level"] == "HIGH"
    assert res["budget_impact"]["status"] == "EXCEEDS_BUDGET"
    assert "exceed your monthly budget" in res["recommendation"]


def test_simulation_caution_near_limit(db_session, test_user):
    # Budget is 2500. 88% of 2500 is 2200
    svc = FinancialSimulatorService(db_session)
    res = svc.simulate_purchase(
        user=test_user,
        purchase_amount=2250.0,
        purchase_category="travel"
    )
    assert res["verdict"] in ["PROCEED_WITH_CAUTION", "UNRECOMMENDED"]
    assert res["budget_impact"]["post_utilization_pct"] >= 85.0
