import pytest
from fastapi.testclient import TestClient
from fastapi import UploadFile, HTTPException
import io

from app.core.security import SecurityValidator
from main import app

client = TestClient(app)


def test_password_strength_validation():
    # Too short
    valid, msg = SecurityValidator.validate_password_strength("Short1!")
    assert not valid
    assert "at least 8 characters" in msg

    # Missing uppercase
    valid, msg = SecurityValidator.validate_password_strength("lowercase123!")
    assert not valid
    assert "uppercase" in msg

    # Missing digits
    valid, msg = SecurityValidator.validate_password_strength("NoDigitsHere!")
    assert not valid
    assert "digit" in msg

    # Missing special char
    valid, msg = SecurityValidator.validate_password_strength("NoSpecialChar123")
    assert not valid
    assert "special character" in msg

    # Valid enterprise password
    valid, msg = SecurityValidator.validate_password_strength("Str0ng!P@ssword2026")
    assert valid
    assert msg is None


def test_upload_file_security_validation():
    # Valid CSV
    valid_csv = UploadFile(filename="transactions.csv", file=io.BytesIO(b"date,amount,category\n"))
    SecurityValidator.validate_upload_file(valid_csv, allowed_extensions={".csv"})

    # Malicious script upload
    malicious_file = UploadFile(filename="malicious_payload.exe", file=io.BytesIO(b"binary content"))
    with pytest.raises(HTTPException) as exc:
        SecurityValidator.validate_upload_file(malicious_file, allowed_extensions={".csv"})
    assert exc.value.status_code == 400
    assert "Unsupported file type" in exc.value.detail


def test_security_headers_in_api_response():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in response.headers
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "X-Request-ID" in response.headers
