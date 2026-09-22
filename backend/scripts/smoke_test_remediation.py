"""
FinMate 2.0 Comprehensive Smoke Test
Validates the full lifecycle flow required by P11:
Register -> Login -> Create transaction -> Import CSV -> Scan receipt ->
Create goal -> View analytics -> View anomaly detection -> View forecast ->
View health score -> View cash flow -> Run purchase simulation ->
Ask AI -> Generate weekly briefing -> Download report -> Export user data ->
Delete demo/test account.
"""

import os
import sys
import io
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app, get_db
import models
from database import engine, SessionLocal
from app.ai.providers import MockVisionProvider, MockProvider, set_vision_provider, set_llm_provider

client = TestClient(app)

def run_smoke_test():
    print("=" * 60)
    print("FINMATE 2.0 — END-TO-END SMOKE TEST (P11 FLOW)")
    print("=" * 60)

    # Use deterministic mock AI providers for offline test stability
    set_llm_provider(MockProvider(default_response="Smoke test deterministic financial advice."))
    set_vision_provider(MockVisionProvider(default_response=json.dumps({
        "merchant": "Smoke Store",
        "amount": 25.50,
        "category": "food",
        "date": "2026-03-20",
        "description": "Smoke receipt extraction"
    })))

    test_email = f"smoke_user_{int(datetime.utcnow().timestamp())}@example.com"
    test_password = "SmokeTestPassword123!"

    # 1. Register
    print("[1/17] Registering new test account...")
    res_reg = client.post("/signup", json={
        "email": test_email,
        "password": test_password,
        "full_name": "Smoke Test User"
    })
    assert res_reg.status_code == 200, f"Register failed: {res_reg.text}"
    user_data = res_reg.json()
    user_id = user_data["user_id"]
    print(f"  -> User registered successfully (ID: {user_id})")

    # 2. Login
    print("[2/17] Authenticating and obtaining JWT bearer token...")
    res_login = client.post("/login", data={
        "username": test_email,
        "password": test_password
    })
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  -> Logged in successfully")

    # 3. Create Transaction
    print("[3/17] Creating transaction...")
    res_tx = client.post("/transactions", headers=headers, json={
        "amount": 48.50,
        "category": "food",
        "description": "Coffee and Lunch",
        "date": (datetime.utcnow() - timedelta(days=1)).isoformat()
    })
    assert res_tx.status_code == 200, f"Create transaction failed: {res_tx.text}"
    tx_id = res_tx.json()["transaction_id"]
    print(f"  -> Transaction created (ID: {tx_id}, Amount: $48.50)")

    # 4. Import CSV
    print("[4/17] Importing transactions via CSV...")
    csv_content = (
        "Date,Description,Amount,Category\n"
        "2026-03-10,Whole Foods Market,120.50,groceries\n"
        "2026-03-11,Shell Gas Station,45.00,transportation\n"
        "2026-03-12,Netflix Subscription,15.99,entertainment\n"
    ).encode("utf-8")
    res_csv = client.post(
        "/import-csv",
        headers=headers,
        files={"file": ("test_import.csv", io.BytesIO(csv_content), "text/csv")}
    )
    assert res_csv.status_code == 200, f"Import CSV failed: {res_csv.text}"
    print(f"  -> CSV imported: {res_csv.json().get('imported', 0)} transactions added")

    # 5. Scan Receipt
    print("[5/17] Scanning receipt image...")
    dummy_img = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    res_receipt = client.post(
        "/scan-receipt",
        headers=headers,
        files={"file": ("receipt.png", io.BytesIO(dummy_img), "image/png")}
    )
    assert res_receipt.status_code == 200, f"Scan receipt failed: {res_receipt.text}"
    print("  -> Receipt processed successfully")

    # 6. Create Goal
    print("[6/17] Creating budget goal...")
    res_goal = client.post("/goals", headers=headers, json={
        "goal_type": "savings",
        "target_amount": 1500.0,
        "deadline": (datetime.utcnow() + timedelta(days=60)).isoformat()
    })
    assert res_goal.status_code == 200, f"Create goal failed: {res_goal.text}"
    goal_id = res_goal.json()["goal_id"]
    print(f"  -> Budget goal created (ID: {goal_id}, Target: $1500.00)")

    # 7. View Analytics
    print("[7/17] Retrieving analytics...")
    res_analytics = client.get("/analytics", headers=headers)
    assert res_analytics.status_code == 200, f"Analytics failed: {res_analytics.text}"
    res_v1_analytics = client.get("/api/v1/analytics/financial-overview", headers=headers)
    assert res_v1_analytics.status_code == 200
    print("  -> Analytics retrieved (both legacy and v1)")

    # 8. View Anomaly Detection
    print("[8/17] Running 3-tier anomaly detection...")
    res_anomalies = client.get("/insights/anomalies", headers=headers)
    assert res_anomalies.status_code == 200, f"Anomalies failed: {res_anomalies.text}"
    res_v1_anom = client.get("/api/v1/analytics/anomalies/layered", headers=headers)
    assert res_v1_anom.status_code == 200
    print("  -> Anomaly detection successfully executed")

    # 9. View Forecast
    print("[9/17] Generating Statsmodels Holt-Winters forecast...")
    res_forecast = client.get("/api/v1/analytics/forecast", headers=headers)
    assert res_forecast.status_code == 200, f"Forecast failed: {res_forecast.text}"
    fc = res_forecast.json()
    assert "forecast_7_day" in fc and "forecast_30_day" in fc and "forecast_90_day" in fc
    print("  -> Holt-Winters 7, 30, and 90 day forecasts generated")

    # 10. View Health Score
    print("[10/17] Computing explainable health score...")
    res_health = client.get("/api/v1/analytics/health-score/explainable", headers=headers)
    assert res_health.status_code == 200, f"Health score failed: {res_health.text}"
    print(f"  -> Health score computed: {res_health.json().get('overall_score')}/100")

    # 11. View Cash Flow
    print("[11/17] Calculating cash flow trajectory...")
    res_cf = client.get("/api/v1/cashflow/projection", headers=headers)
    assert res_cf.status_code == 200, f"Cash flow failed: {res_cf.text}"
    print("  -> 30-day forward cash flow projection retrieved")

    # 12. Run Purchase Simulation
    print("[12/17] Running purchase simulation...")
    res_sim = client.post("/simulation/purchase", headers=headers, json={
        "purchase_amount": 150.0,
        "purchase_category": "shopping",
        "description": "Smart Watch"
    })
    assert res_sim.status_code == 200, f"Simulation failed: {res_sim.text}"
    print("  -> Purchase simulation executed successfully")

    # 13. Ask AI
    print("[13/17] Interacting with controlled AI agent...")
    res_ai = client.post("/api/v1/ai/chat", headers=headers, json={
        "message": "What is my spending summary?"
    })
    assert res_ai.status_code == 200, f"Ask AI failed: {res_ai.text}"
    print("  -> AI reply grounded and received")

    # 14. Generate Weekly Briefing
    print("[14/17] Generating weekly briefing...")
    res_brief = client.get("/api/v1/analytics/briefing/weekly", headers=headers)
    assert res_brief.status_code == 200, f"Weekly briefing failed: {res_brief.text}"
    print("  -> Weekly briefing generated")

    # 15. Download Report
    print("[15/17] Downloading financial report...")
    res_rep = client.get("/api/v1/analytics/report/download", headers=headers)
    assert res_rep.status_code == 200, f"Download report failed: {res_rep.text}"
    print("  -> Financial report downloaded successfully")

    # 16. Export User Data
    print("[16/17] Exporting personal user data...")
    res_export = client.get("/api/v1/user/export-data", headers=headers)
    assert res_export.status_code == 200, f"Export data failed: {res_export.text}"
    exp_data = res_export.json()
    assert "user_profile" in exp_data and "transactions" in exp_data and "goals" in exp_data
    print("  -> User data export verified")

    # 17. Delete Account
    print("[17/17] Deleting demo/test account...")
    res_del = client.delete("/api/v1/user/account", headers=headers)
    assert res_del.status_code == 200, f"Account deletion failed: {res_del.text}"
    print("  -> Account deletion succeeded")

    # Verify complete erasure
    db = SessionLocal()
    assert db.query(models.User).filter_by(user_id=user_id).first() is None
    assert db.query(models.Transaction).filter_by(user_id=user_id).count() == 0
    assert db.query(models.BudgetGoal).filter_by(user_id=user_id).count() == 0
    assert db.query(models.ReceiptPending).filter_by(user_id=user_id).count() == 0
    db.close()
    print("  -> Verified zero residual user records in database")

    print("\n" + "=" * 60)
    print("ALL 17 P11 SMOKE TEST STEPS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_smoke_test()
