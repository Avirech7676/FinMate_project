import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application configuration with backward compatibility for all existing environment variables."""
    PROJECT_NAME: str = "FinMate 2.0"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./finmate.db")

    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

    # JWT Authentication
    _raw_secret: str = os.getenv("SECRET_KEY", "")
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        if not _raw_secret or len(_raw_secret) < 32 or "change_this" in _raw_secret.lower() or "dev" in _raw_secret.lower():
            raise RuntimeError(
                "CRITICAL SECURITY ERROR: Production startup aborted. "
                "SECRET_KEY must be set in the environment and must be a secure random string of at least 32 characters."
            )
        SECRET_KEY: str = _raw_secret
    else:
        # Development / Testing environment
        # Must come from environment configuration (.env or system env)
        if not _raw_secret:
            # Non-production fallback with explicit warning
            import warnings
            warnings.warn(
                "SECURITY WARNING: SECRET_KEY is not set in the environment. "
                "Using an explicit local development key. Please configure SECRET_KEY in your .env file.",
                RuntimeWarning,
                stacklevel=2
            )
            SECRET_KEY: str = "finmate-dev-only-static-secret-key-32chars-for-testing"
        else:
            SECRET_KEY: str = _raw_secret

    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Email Service
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "noreply@finmate.app")

    # CORS & Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_MINUTES: int = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "1"))

    # Optional services
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    PLAID_CLIENT_ID: str = os.getenv("PLAID_CLIENT_ID", "")
    PLAID_SECRET: str = os.getenv("PLAID_SECRET", "")
    PLAID_ENV: str = os.getenv("PLAID_ENV", "sandbox")

settings = Settings()
