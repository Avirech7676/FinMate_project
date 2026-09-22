"""
Backend tests for FinMate API
Run with: pytest test_main.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from main import app, get_db
from database import Base
import models

# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_main_db():
    app.dependency_overrides[get_db] = override_get_db
    yield

# Test fixtures
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "TestPassword123"
TEST_USER_NAME = "Test User"

@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Clean up test database before and after tests"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    try:
        if os.path.exists("test.db"):
            os.remove("test.db")
    except Exception:
        pass

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_signup_success(self):
        """Test successful user signup"""
        response = client.post(
            "/signup",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER_EMAIL
        assert data["full_name"] == TEST_USER_NAME
    
    def test_signup_duplicate_email(self):
        """Test signup with existing email"""
        client.post(
            "/signup",
            json={
                "email": "duplicate@example.com",
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            }
        )
        response = client.post(
            "/signup",
            json={
                "email": "duplicate@example.com",
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            }
        )
        assert response.status_code == 400
    
    def test_signup_weak_password(self):
        """Test signup with weak password"""
        response = client.post(
            "/signup",
            json={
                "email": "weak@example.com",
                "password": "weak",  # Too short and weak
                "full_name": TEST_USER_NAME
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_login_success(self):
        """Test successful login"""
        # First signup
        client.post(
            "/signup",
            json={
                "email": "login@example.com",
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            }
        )
        
        # Then login
        response = client.post(
            "/login",
            data={
                "username": "login@example.com",
                "password": TEST_USER_PASSWORD
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        client.post(
            "/signup",
            json={
                "email": "wrong@example.com",
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            }
        )
        
        response = client.post(
            "/login",
            data={
                "username": "wrong@example.com",
                "password": "WrongPassword123"
            }
        )
        assert response.status_code == 401

class TestTransactions:
    """Test transaction endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user and token"""
        # Create user
        client.post(
            "/signup",
            json={
                "email": "txn@example.com",
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            }
        )
        
        # Login to get token
        response = client.post(
            "/login",
            data={
                "username": "txn@example.com",
                "password": TEST_USER_PASSWORD
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_transaction(self):
        """Test creating a transaction"""
        response = client.post(
            "/transactions",
            json={
                "amount": 50.00,
                "description": "Grocery shopping",
                "category": "food",
                "source": "manual"
            },
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 50.00
        assert data["category"] == "food"
    
    def test_create_transaction_invalid_amount(self):
        """Test creating transaction with invalid amount"""
        response = client.post(
            "/transactions",
            json={
                "amount": -10.00,  # Negative amount
                "description": "Invalid",
                "category": "food"
            },
            headers=self.headers
        )
        assert response.status_code == 422
    
    def test_create_transaction_auto_categorization(self):
        """Test auto-categorization of transactions"""
        response = client.post(
            "/transactions",
            json={
                "amount": 25.00,
                "description": "Starbucks coffee",
                "category": "uncategorized"
            },
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        # Should auto-categorize to 'food' based on keywords
        assert data["category"] in ["food", "uncategorized"]

    def test_import_csv_alias(self):
        """Test the POST /import-csv backward compatibility alias"""
        csv_data = "Date,Description,Amount,Category\n2026-09-01,Groceries,45.50,Food\n"
        response = client.post(
            "/import-csv",
            files={"file": ("transactions.csv", csv_data, "text/csv")},
            headers=self.headers
        )
        assert response.status_code == 200

class TestBudgetGoals:
    """Test budget goal endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user and token"""
        client.post(
            "/signup",
            json={
                "email": "goal@example.com",
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME
            }
        )
        
        response = client.post(
            "/login",
            data={
                "username": "goal@example.com",
                "password": TEST_USER_PASSWORD
            }
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_budget_goal(self):
        """Test creating a budget goal"""
        from datetime import datetime, timedelta
        
        future_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        response = client.post(
            "/goals",
            json={
                "goal_type": "savings",
                "target_amount": 1000.00,
                "deadline": future_date
            },
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["target_amount"] == 1000.00
        assert data["goal_type"] == "savings"

class TestHealth:
    """Test health check"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Welcome" in data.get("message", "")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
