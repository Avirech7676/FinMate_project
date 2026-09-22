import sys
import traceback
try:
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    response = client.post("/signup", json={"email": "testdb@test.com", "password":"Password123", "full_name":"Test User"})
    print("Status code:", response.status_code)
    print("Response text:", response.text)
except Exception as e:
    traceback.print_exc()
