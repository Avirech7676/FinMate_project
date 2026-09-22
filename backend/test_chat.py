import sys
import traceback
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from fastapi.testclient import TestClient
    from main import app
    import auth
    
    client = TestClient(app)
    
    # Get a token for our test user
    token = auth.create_access_token(data={"sub": "testdb@test.com"})
    
    print(f"Testing chat with token...")
    response = client.post(
        "/chat", 
        json={"message": "Hello FinMate!", "roast_mode": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    print("Status code:", response.status_code)
    print("Response text:", response.text)
except Exception as e:
    traceback.print_exc()
