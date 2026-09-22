"""
Utility functions and middleware
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
from datetime import datetime
import re
import hashlib
from typing import Optional, Iterable, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests. Please try again later."}
    )

class ValidationError(HTTPException):
    """Custom validation error"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message
        )

class BusinessLogicError(HTTPException):
    """Custom business logic error"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

def log_action(action: str, user_id: int, details: str = "", status_code: int = 200):
    """Log user actions for debugging and auditing"""
    timestamp = datetime.utcnow().isoformat()
    logger.info(f"[{timestamp}] User {user_id}: {action} - {details} (Status: {status_code})")

def validate_amount(amount: float, max_amount: float = 999999.99) -> None:
    """Validate transaction amount"""
    if amount <= 0:
        raise ValidationError("Amount must be positive")
    if amount > max_amount:
        raise ValidationError(f"Amount cannot exceed ${max_amount}")
    if '.' in str(amount) and len(str(amount).split('.')[-1]) > 2:
        raise ValidationError("Amount can only have up to 2 decimal places")

def validate_category(category: str, allowed_categories: list = None) -> None:
    """Validate transaction category"""
    if not category:
        raise ValidationError("Category is required")
    if not isinstance(category, str) or len(category.strip()) == 0:
        raise ValidationError("Category must be a non-empty string")

def safe_json_load(json_string: str, default: dict = None) -> dict:
    """Safely load JSON with fallback"""
    import json
    try:
        return json.loads(json_string)
    except:
        return default or {}

def calculate_health_score(total_spent: float, monthly_income: float = None) -> dict:
    """
    Calculate financial health score
    Returns dict with score, label, and color
    """
    # Default scoring if no income
    if not monthly_income:
        if total_spent == 0:
            return {"score": 75, "label": "Good", "color": "#00d4aa"}
        if total_spent < 500:
            return {"score": 90, "label": "Excellent", "color": "#00d4aa"}
        if total_spent < 1500:
            return {"score": 72, "label": "Good", "color": "#4f8fe8"}
        if total_spent < 3000:
            return {"score": 55, "label": "Fair", "color": "#f59e0b"}
        if total_spent < 5000:
            return {"score": 38, "label": "Needs Work", "color": "#f97316"}
        return {"score": 20, "label": "Critical", "color": "#ff4d6d"}
    
    # Income-based scoring
    spending_ratio = total_spent / monthly_income
    
    if spending_ratio <= 0.2:
        return {"score": 95, "label": "Excellent", "color": "#00d4aa"}
    elif spending_ratio <= 0.4:
        return {"score": 85, "label": "Good", "color": "#4f8fe8"}
    elif spending_ratio <= 0.6:
        return {"score": 70, "label": "Fair", "color": "#f59e0b"}
    elif spending_ratio <= 0.8:
        return {"score": 50, "label": "Needs Work", "color": "#f97316"}
    else:
        return {"score": 30, "label": "Critical", "color": "#ff4d6d"}

def _merchant_category_dictionary() -> Dict[str, str]:
    """
    Lightweight "ML-style" merchant classifier.

    Keys are normalized merchant tokens (see normalize_merchant_key),
    values are canonical category slugs used across the app.

    This gives us a deterministic, hackathon-friendly approximation of a
    trained classifier without adding a model dependency.
    """
    return {
        # Food & dining
        "starbucks": "food",
        "mcdonald s": "food",
        "kfc": "food",
        "dominos": "food",
        "ubereats": "food",
        "swiggy": "food",
        "zomato": "food",
        "doordash": "food",
        "foodpanda": "food",
        "pizza hut": "food",
        # Groceries / supermarkets
        "walmart": "food",
        "costco": "food",
        "tesco": "food",
        "big bazaar": "food",
        "dmart": "food",
        "aldi": "food",
        "lidl": "food",
        "target": "shopping",
        # Transport
        "uber": "transportation",
        "ola": "transportation",
        "lyft": "transportation",
        "bolt": "transportation",
        "shell": "transportation",
        "chevron": "transportation",
        # Entertainment / subscriptions
        "netflix": "entertainment",
        "spotify": "entertainment",
        "youtube premium": "entertainment",
        "amazon prime": "entertainment",
        "disney plus": "entertainment",
        "playstation": "entertainment",
        "xbox": "entertainment",
        # Utilities / bills
        "at t": "utilities",
        "verizon": "utilities",
        "comcast": "utilities",
        "xfinity": "utilities",
        "jio fiber": "utilities",
        "airtel": "utilities",
        # Healthcare / fitness
        "pharmacy": "healthcare",
        "walgreens": "healthcare",
        "cvs": "healthcare",
        "boots": "healthcare",
        "planet fitness": "healthcare",
        "cult fit": "healthcare",
        "anytime fitness": "healthcare",
        # Shopping / ecommerce
        "amazon": "shopping",
        "flipkart": "shopping",
        "myntra": "shopping",
        "ikea": "shopping",
        "h m": "shopping",
        "zara": "shopping",
    }


def suggest_category(description: str) -> str:
    """
    Simple category suggestion that combines:
    - A merchant dictionary (normalized via normalize_merchant_key)
    - Keyword-based fallbacks

    This behaves like a tiny ML classifier but stays fully deterministic.
    """
    description = description or ""
    description_lower = description.lower()

    # 1) Merchant dictionary pass (treats description as merchant-ish string)
    merchant_key = normalize_merchant_key(description)
    merchant_map = _merchant_category_dictionary()
    if merchant_key in merchant_map:
        return merchant_map[merchant_key]

    # 2) Keyword-based fallback
    keywords = {
        "food": ["grocery", "restaurant", "cafe", "coffee", "pizza", "burger", "food", "lunch", "dinner", "breakfast", "market", "supermarket"],
        "transportation": ["gas", "fuel", "parking", "uber", "lyft", "taxi", "cab", "bus", "train", "metro", "car", "vehicle", "tolls", "transit"],
        "entertainment": ["movie", "cinema", "concert", "game", "spotify", "netflix", "gaming", "show", "entertainment", "ticket", "theatre"],
        "utilities": ["electricity", "water", "internet", "phone", "utility", "bill", "wifi", "broadband"],
        "healthcare": ["pharmacy", "doctor", "hospital", "medicine", "health", "dental", "gym", "medical", "clinic"],
        "shopping": ["clothing", "clothes", "apparel", "mall", "store", "shop", "purchase", "online order", "ecommerce"],
        "housing": ["rent", "mortgage", "loan emi", "emi"],
        "other": []
    }

    for category, words in keywords.items():
        if any(word in description_lower for word in words):
            return category

    return "other"


_MONEY_CLEAN_RE = re.compile(r"[^\d\-\(\)\.,]")


def parse_money(value) -> Optional[float]:
    """
    Best-effort money parser for CSV/receipt ingestion.
    Handles: ₹1,234.50, $1,234.50, (1,234.50), -1234.5, "1.234,50" (EU-ish).
    Returns float or None if not parseable.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none", "null"}:
        return None

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]

    s = _MONEY_CLEAN_RE.sub("", s)
    s = s.strip()
    if not s:
        return None

    if s.count(",") > 0 and s.count(".") == 0:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")

    try:
        amt = float(s)
    except Exception:
        return None

    if negative or amt < 0:
        amt = -abs(amt)
    return amt


def normalize_header(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def pick_first(mapping: dict, keys: Iterable[str]) -> Optional[str]:
    for k in keys:
        if k in mapping:
            return mapping[k]
    return None


def normalize_merchant_key(description: str) -> str:
    """
    Best-effort normalization to group recurring merchants.
    Intentionally simple and deterministic for hackathon reliability.
    """
    if not description:
        return "unknown"
    s = description.lower()
    s = re.sub(r"(receipt:)\s*", "", s)
    s = re.sub(r"\d+", "", s)
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Keep first few tokens to avoid overfitting to long descriptors
    tokens = s.split(" ")
    return " ".join(tokens[:4]) if tokens else "unknown"


def make_candidate_id(user_id: int, merchant_key: str) -> str:
    raw = f"{user_id}:{merchant_key}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]

def generate_spending_summary(transactions: list) -> dict:
    """Generate summary statistics from transactions"""
    if not transactions:
        return {
            "total": 0,
            "count": 0,
            "average": 0,
            "by_category": {},
            "highest_transaction": None
        }
    
    from collections import defaultdict
    total = sum(t.amount for t in transactions)
    by_category = defaultdict(float)
    
    for t in transactions:
        by_category[t.category] += t.amount
    
    highest = max(transactions, key=lambda x: x.amount)
    
    return {
        "total": round(total, 2),
        "count": len(transactions),
        "average": round(total / len(transactions), 2),
        "by_category": {cat: round(amount, 2) for cat, amount in by_category.items()},
        "highest_transaction": {
            "amount": highest.amount,
            "category": highest.category,
            "description": highest.description,
            "date": highest.date.isoformat() if highest.date else None
        }
    }
