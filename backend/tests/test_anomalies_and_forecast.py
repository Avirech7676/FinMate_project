import pytest
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import models
from app.analytics.anomalies import LayeredAnomalyDetector
from app.analytics.forecasting import SpendingForecaster

def test_anomaly_detection_rule_level():
    now = datetime.utcnow()
    # Baseline normal transactions around $10-$20
    txns = [
        models.Transaction(transaction_id=1, amount=15.0, category="food", description="Lunch", date=now - timedelta(days=10)),
        models.Transaction(transaction_id=2, amount=18.0, category="food", description="Breakfast", date=now - timedelta(days=9)),
        models.Transaction(transaction_id=3, amount=12.0, category="food", description="Coffee", date=now - timedelta(days=8)),
        models.Transaction(transaction_id=4, amount=20.0, category="food", description="Dinner", date=now - timedelta(days=7)),
        # Severe outlier > 3x median and >= 150
        models.Transaction(transaction_id=5, amount=220.0, category="food", description="Luxury Banquet", date=now - timedelta(days=1)),
    ]

    anomalies = LayeredAnomalyDetector.detect_anomalies(txns)
    assert len(anomalies) >= 1
    anom = next(a for a in anomalies if a.transaction_id == 5)
    assert anom.level in ["rule", "statistical"]
    assert anom.anomaly_score > 0.5
    assert "food" in anom.reason.lower()

def test_spending_forecasting_horizons():
    base_date = datetime(2026, 8, 1)
    txns = []
    # 30 days of consistent $50 daily spending
    for i in range(30):
        t_date = base_date + timedelta(days=i)
        txns.append(models.Transaction(
            transaction_id=100 + i,
            amount=50.0,
            category="groceries" if i % 2 == 0 else "transit",
            description="Daily Expense",
            date=t_date
        ))

    forecast = SpendingForecaster.generate_forecast(txns, monthly_income=3000.0)

    assert "forecast_7_day" in forecast
    assert "forecast_30_day" in forecast
    assert "forecast_90_day" in forecast

    f7 = forecast["forecast_7_day"]
    f30 = forecast["forecast_30_day"]
    f90 = forecast["forecast_90_day"]

    assert f7["horizon_days"] == 7
    # With $50/day, 7-day should be approx 350
    assert 300.0 <= f7["projected_spending"] <= 400.0
    # 30-day approx 1500
    assert 1300.0 <= f30["projected_spending"] <= 1700.0
    # 90-day approx 4500
    assert 4000.0 <= f90["projected_spending"] <= 5000.0

    # Net cash flow calculation (income 3000/mo = 100/day, spend = 50/day => positive cash flow)
    assert f30["net_cash_flow"] > 0
    assert f30["cash_flow_risk"] == "low"
    assert "model_metadata" in forecast
    assert len(forecast["model_metadata"]["assumptions"]) >= 2
