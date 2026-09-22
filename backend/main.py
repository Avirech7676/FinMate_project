from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Union
from datetime import timedelta, datetime
import pandas as pd
import io
import os
import google.generativeai as genai
import json
from database import engine, Base, get_db
import models
import schemas
import auth
import gamification
import ai_insights
import utils
from email_service import email_service
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from collections import defaultdict
from debate_cache import TTLCache
from providers.web_search import default_offer_providers
import debate
from app.core.middleware import ObservabilityMiddleware
from app.core.config import settings
from app.api.v1.router import api_v1_router

def _month_window(month_offset: int = 0):
    """
    Returns (start_datetime, end_datetime) for the month offset from current month.
    month_offset=0 => current month, -1 => last month.
    """
    now = datetime.utcnow()
    first_this_month = datetime(now.year, now.month, 1)
    # move to target month
    y = first_this_month.year
    m = first_this_month.month + month_offset
    while m <= 0:
        y -= 1
        m += 12
    while m >= 13:
        y += 1
        m -= 12
    start = datetime(y, m, 1)
    # next month
    nm = m + 1
    ny = y
    if nm == 13:
        nm = 1
        ny += 1
    end = datetime(ny, nm, 1)
    return start, end

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Note: Database migrations are managed via Alembic in production (python -m alembic upgrade head).
# Base.metadata.create_all is strictly reserved for isolated test and benchmark databases.

app = FastAPI(title="FinMate API", description="Your AI-powered financial companion")

# Add rate limiter
from utils import limiter, rate_limit_exceeded_handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add CORS routing limits (env-driven for deploy safety)
frontend_urls_env = os.getenv("FRONTEND_URL", "").strip()
frontend_urls = [u.strip() for u in frontend_urls_env.split(",") if u.strip()]
if not frontend_urls:
    frontend_urls = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ObservabilityMiddleware)

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Debate Mode caches (in-memory, demo-friendly)
_offers_cache = TTLCache(ttl_s=20 * 60, max_items=256)

# Custom error handlers
@app.exception_handler(utils.ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(utils.BusinessLogicError)
async def business_logic_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

app.include_router(api_v1_router)

from app.api.v1.simulation import PurchaseSimulationRequest
from app.services.simulation_service import FinancialSimulatorService

@app.post("/simulation/purchase")
def simulate_purchase_root(
    req: PurchaseSimulationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Simulate purchase impact on budget, cash flow, and goals."""
    return FinancialSimulatorService(db).simulate_purchase(
        user=current_user,
        purchase_amount=req.purchase_amount,
        purchase_category=req.purchase_category or "shopping",
        purchase_date=req.purchase_date,
        description=req.description
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to FinMate API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    return {"status": "ok"}

@app.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --- AUTHENTICATION ROUTES ---
from app.services.user_service import UserService
from app.services.transaction_service import TransactionService
from app.services.goal_service import GoalService

@app.post("/signup", response_model=schemas.UserOut)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers new user via shared UserService"""
    return UserService(db).register_user(user)

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user via shared UserService"""
    user = UserService(db).authenticate_user(form_data.username, form_data.password)
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- TRANSACTION & IMPORT ROUTES ---

@app.post("/transactions", response_model=schemas.TransactionOut)
def create_transaction(
    transaction: schemas.TransactionCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    """Create transaction via shared TransactionService"""
    return TransactionService(db).create_transaction(current_user, transaction)

@app.get("/transactions")
def get_all_transactions(
    limit: int = 100,
    offset: int = 0,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Retrieve transactions via shared TransactionService"""
    transactions = TransactionService(db).list_transactions(
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
        category=category,
        search=search
    )
    return [schemas.TransactionOut.model_validate(t).model_dump() for t in transactions]

@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Update transaction via shared TransactionService"""
    return TransactionService(db).update_transaction(transaction_id, current_user.user_id, transaction)

@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Delete transaction via shared TransactionService"""
    return TransactionService(db).delete_transaction(transaction_id, current_user.user_id)

def _detect_source_currency_from_headers_and_sample(df: pd.DataFrame) -> str | None:
    """
    Best-effort currency detection based on headers and sample values.
    This is used for preview and as a default when the frontend doesn't
    explicitly tell us the CSV's native currency.
    """
    headers = " ".join([str(c).lower() for c in df.columns])
    text_blob = headers
    sample_rows = df.head(10).to_dict(orient="records")
    for row in sample_rows:
        for v in row.values():
            if isinstance(v, str):
                text_blob += " " + v
    text_blob = text_blob.lower()

    if any(tok in text_blob for tok in ["₹", " inr", "rs ", " rs.", " rs-"]):
        return "INR"
    if any(tok in text_blob for tok in ["£", " gbp"]):
        return "GBP"
    if any(tok in text_blob for tok in ["€", " eur"]):
        return "EUR"
    if any(tok in text_blob for tok in ["usd", "$"]):
        return "USD"
    return None


@app.post("/upload-csv/preview")
async def preview_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Lightweight preview endpoint used by the frontend before import.

    - Detects likely date / description / amount / debit / credit columns
    - Guesses a source currency
    - Returns a few normalized sample rows
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    content = await file.read()
    # Decode robustly (reuse the same logic as the main import)
    csv_content = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            csv_content = content.decode(enc)
            break
        except Exception:
            continue
    if csv_content is None:
        raise HTTPException(status_code=400, detail="Could not decode CSV file.")

    sample = csv_content[:5000]
    delim = ","
    if sample.count(";") > sample.count(",") and sample.count(";") >= 3:
        delim = ";"
    elif sample.count("\t") > sample.count(",") and sample.count("\t") >= 3:
        delim = "\t"

    df = pd.read_csv(
        io.StringIO(csv_content),
        sep=delim,
        dtype=str,
        keep_default_na=False,
        engine="python",
    )

    colmap = {utils.normalize_header(c): c for c in df.columns}

    date_col = utils.pick_first(
        colmap,
        [
            "date",
            "transaction date",
            "posted date",
            "value date",
            "txn date",
            "trans date",
            "booking date",
            "time",
            "date & time",
        ],
    )
    desc_col = utils.pick_first(
        colmap,
        [
            "description",
            "narration",
            "details",
            "transaction details",
            "particulars",
            "merchant",
            "name",
            "remarks",
            "reference",
            "payee",
            "transaction description",
        ],
    )
    amount_col = utils.pick_first(
        colmap,
        [
            "amount",
            "amt",
            "value",
            "transaction amount",
            "amount inr",
            "amount_inr",
            "inr amount",
            "amount (inr)",
        ],
    )
    debit_col = utils.pick_first(
        colmap,
        [
            "debit",
            "withdrawal",
            "withdrawals",
            "dr",
            "debit amount",
            "amount (dr)",
        ],
    )
    credit_col = utils.pick_first(
        colmap,
        [
            "credit",
            "deposit",
            "deposits",
            "cr",
            "credit amount",
            "amount (cr)",
        ],
    )
    currency_col = utils.pick_first(colmap, ["currency", "ccy"])

    detected_currency = _detect_source_currency_from_headers_and_sample(df)

    # Build a tiny normalized sample preview (no DB writes)
    samples = []
    for _, row in df.head(5).iterrows():
        raw_date = row.get(date_col) if date_col else None
        raw_desc = row.get(desc_col) if desc_col else None
        raw_amount = row.get(amount_col) if amount_col else None
        if raw_amount is None and (debit_col or credit_col):
            # Best effort: prefer debit, else credit
            d = row.get(debit_col) if debit_col else None
            c = row.get(credit_col) if credit_col else None
            raw_amount = d or c
        samples.append(
            {
                "date": raw_date,
                "description": raw_desc,
                "amount_raw": raw_amount,
            }
        )

    return {
        "status": "success",
        "columns": list(df.columns),
        "detected": {
            "date_column": date_col,
            "description_column": desc_col,
            "amount_column": amount_col,
            "debit_column": debit_col,
            "credit_column": credit_col,
            "currency_column": currency_col,
            "source_currency": detected_currency or current_user.currency,
        },
        "sample_rows": samples,
    }


@app.post("/import-csv")
@app.post("/upload-csv")
async def upload_transactions_csv(
    file: UploadFile = File(...),
    source_currency: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Main CSV import endpoint.

    - Uses robust column detection for date/description/amount/debit/credit
    - Optionally uses a source_currency provided by the frontend (confirmed by user)
    - Falls back to deterministic parsing when AI is unavailable or the file is large
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    content = await file.read()
    try:
        # Decode robustly (bank exports are often UTF-8-SIG or Windows-1252)
        csv_content = None
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                csv_content = content.decode(enc)
                break
            except Exception:
                continue
        if csv_content is None:
            raise HTTPException(status_code=400, detail="Could not decode CSV file.")

        # Sniff delimiter (comma vs semicolon vs tab)
        sample = csv_content[:5000]
        delim = ","
        if sample.count(";") > sample.count(",") and sample.count(";") >= 3:
            delim = ";"
        elif sample.count("\t") > sample.count(",") and sample.count("\t") >= 3:
            delim = "\t"

        df = pd.read_csv(
            io.StringIO(csv_content),
            sep=delim,
            dtype=str,
            keep_default_na=False,
            engine="python",
        )
        
        def fallback_import(df_in: pd.DataFrame, override_currency: str | None = None):
            """
            Non-AI fallback for demo reliability: best-effort column mapping + parsing.
            Expected columns: date, description, amount, category (any casing).
            """
            colmap = {utils.normalize_header(c): c for c in df_in.columns}

            date_col = utils.pick_first(colmap, [
                "date", "transaction date", "posted date", "value date", "txn date", "trans date",
                "booking date", "time", "date & time"
            ])
            desc_col = utils.pick_first(colmap, [
                "description", "narration", "details", "transaction details", "particulars",
                "merchant", "name", "remarks", "reference", "payee", "transaction description"
            ])

            # Amount patterns vary a lot: amount, debit/credit, withdrawal/deposit, dr/cr, etc.
            amount_col = utils.pick_first(colmap, [
                "amount", "amt", "value", "transaction amount",
                "amount inr", "amount_inr", "inr amount", "amount (inr)"
            ])
            debit_col = utils.pick_first(colmap, ["debit", "withdrawal", "withdrawals", "dr", "debit amount", "amount (dr)"])
            credit_col = utils.pick_first(colmap, ["credit", "deposit", "deposits", "cr", "credit amount", "amount (cr)"])
            category_col = utils.pick_first(colmap, ["category"])
            type_col = utils.pick_first(colmap, ["type", "txn type", "transaction type", "dr/cr", "debit/credit"])
            currency_col = utils.pick_first(colmap, ["currency", "ccy"])

            transactions_added_local = 0
            detected_src_currency = override_currency or _detect_source_currency_from_headers_and_sample(df_in)

            conversion_rates = {
                ('INR', 'USD'): 0.012,
                ('USD', 'INR'): 83.0,
                ('EUR', 'USD'): 1.1,
                ('USD', 'EUR'): 0.91,
                ('GBP', 'USD'): 1.27,
                ('USD', 'GBP'): 0.79
            }

            for _, row in df_in.iterrows():
                try:
                    raw_date = row.get(date_col) if date_col else None
                    try:
                        date_val = pd.to_datetime(raw_date, errors="coerce").date() if raw_date else None
                    except Exception:
                        date_val = None
                    if not date_val:
                        date_val = datetime.now().date()

                    raw_desc = row.get(desc_col) if desc_col else None
                    description = str(raw_desc) if raw_desc not in (None, "", "nan") else "Unknown"

                    amount_signed = None
                    if amount_col:
                        amount_signed = utils.parse_money(row.get(amount_col))

                    if amount_signed is None and (debit_col or credit_col):
                        d = utils.parse_money(row.get(debit_col)) if debit_col else None
                        c = utils.parse_money(row.get(credit_col)) if credit_col else None
                        if d is not None and abs(d) > 0:
                            amount_signed = -abs(d)
                        elif c is not None and abs(c) > 0:
                            amount_signed = abs(c)

                    if amount_signed is None and type_col and amount_col:
                        t = str(row.get(type_col) or "").strip().lower()
                        base = utils.parse_money(row.get(amount_col))
                        if base is not None:
                            if t in {"dr", "debit", "d"}:
                                amount_signed = -abs(base)
                            elif t in {"cr", "credit", "c"}:
                                amount_signed = abs(base)
                            else:
                                amount_signed = base

                    if amount_signed is None:
                        continue

                    # Store expenses as positive amounts (FinMate model assumes spending)
                    amount = abs(float(amount_signed))
                    if amount <= 0:
                        continue

                    category = str(row.get(category_col)).lower() if category_col and row.get(category_col) not in (None, "", "nan") else utils.suggest_category(description)
                    row_currency = str(row.get(currency_col)).upper() if currency_col and row.get(currency_col) not in (None, "", "nan") else None
                    src_currency = (override_currency or row_currency or detected_src_currency or current_user.currency).upper()

                    if src_currency != current_user.currency:
                        rate = conversion_rates.get((src_currency, current_user.currency), 1.0)
                        amount = amount * rate

                    txn = models.Transaction(
                        user_id=current_user.user_id,
                        amount=amount,
                        description=description,
                        category=category,
                        date=date_val,
                        source="import"
                    )
                    db.add(txn)
                    transactions_added_local += 1
                except Exception:
                    continue

            db.commit()
            return transactions_added_local
        
        # Use Gemini to normalize the ENTIRE CSV in one call (fast) but fall back safely.
        prompt = f"""
You are a CSV data normalizer. Given a CSV with transaction data, extract and normalize ALL rows to this exact format:
Date, Description, Amount, Category, Currency

Rules:
- Date: Convert to YYYY-MM-DD format
- Description: The merchant or transaction description
- Amount: Positive number only (remove currency symbols, convert to float)
- Category: One of: food, transportation, entertainment, utilities, healthcare, shopping, housing, other (lowercase)
- Currency: Detect currency from symbols/text (USD, INR, EUR, GBP, etc.) - if unclear, use "USD"

Here's the FULL CSV data:
{df.to_csv(index=False)}

Column names: {', '.join(df.columns.tolist())}

Return ONLY a JSON array of objects with keys: date, description, amount, category, currency
Example: [{{"date": "2024-03-12", "description": "Starbucks", "amount": 5.50, "category": "food", "currency": "USD"}}, {{"date": "2024-03-11", "description": "Uber", "amount": 15.00, "category": "transportation", "currency": "USD"}}]

Process ALL rows in the CSV. If you can't determine a field, use:
- date: today's date
- description: "Unknown"
- amount: 0.0
- category: "other"
- currency: "USD"
"""
        
        # Demo-safe guardrails: prefer deterministic parser; only use AI for small files.
        if (not GEMINI_API_KEY) or len(df) > 200:
            imported = fallback_import(df, override_currency=source_currency)
            return {
                "status": "success",
                "imported": imported,
                "message": "Imported transactions with fallback parser (AI disabled or file too large).",
                "detected_currency": None
            }

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            
            # Parse Gemini response
            import json
            import re
            
            # Extract JSON from response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            response_text = re.sub(r'```json\s*|\s*```', '', response_text)

            try:
                normalized_data = json.loads(response_text)
            except Exception:
                # Try to extract first JSON array from messy output
                m = re.search(r"\[[\s\S]*\]", response_text)
                if m:
                    normalized_data = json.loads(m.group(0))
                else:
                    imported = fallback_import(df, override_currency=source_currency)
                    return {
                        "status": "success",
                        "imported": imported,
                        "message": "Imported transactions with fallback parser (AI response invalid).",
                        "detected_currency": None
                    }
        except Exception:
            imported = fallback_import(df, override_currency=source_currency)
            return {
                "status": "success",
                "imported": imported,
                "message": "Imported transactions with fallback parser (AI unavailable).",
                "detected_currency": None
            }
        
        # Process normalized data
        transactions_added = 0
        detected_currency = None
        
        for row_data in normalized_data:
            try:
                # Parse date
                try:
                    date_val = pd.to_datetime(row_data['date']).date()
                except:
                    date_val = datetime.now().date()
                
                amount = float(row_data['amount'])
                description = str(row_data['description'])
                category = str(row_data['category']).lower()
                currency = row_data.get('currency', 'USD')
                
                # Track detected currency (respect explicit source_currency override)
                if not detected_currency:
                    detected_currency = source_currency or currency
                
                # Convert amount if currency doesn't match user's currency
                effective_src_currency = (source_currency or currency).upper()
                if effective_src_currency != current_user.currency:
                    # Simple conversion rates (in production, use real-time rates)
                    conversion_rates = {
                        ('INR', 'USD'): 0.012,
                        ('USD', 'INR'): 83.0,
                        ('EUR', 'USD'): 1.1,
                        ('USD', 'EUR'): 0.91,
                        ('GBP', 'USD'): 1.27,
                        ('USD', 'GBP'): 0.79
                    }
                    
                    rate = conversion_rates.get((effective_src_currency, current_user.currency), 1.0)
                    amount = amount * rate
                
                txn = models.Transaction(
                    user_id=current_user.user_id,
                    amount=amount,
                    description=description,
                    category=category,
                    date=date_val,
                    source="import"
                )
                db.add(txn)
                transactions_added += 1
            except Exception as row_error:
                # Skip problematic rows
                continue
        
        db.commit()
        
        message = f"Successfully imported {transactions_added} transactions using AI normalization"
        if detected_currency and detected_currency != current_user.currency:
            message += f" (converted from {detected_currency} to {current_user.currency})"
        
        return {
            "status": "success", 
            "imported": transactions_added, 
            "message": message,
            "detected_currency": detected_currency
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

@app.get("/analytics/weekly")
def get_weekly_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # Get transactions from last 4 weeks
    end_date = datetime.now().date()
    start_date = end_date - timedelta(weeks=4)
    
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.user_id,
        models.Transaction.date >= start_date,
        models.Transaction.date <= end_date
    ).all()
    
    # Group by week and category
    weekly_data = []
    for week_offset in range(4):
        week_start = end_date - timedelta(weeks=3-week_offset)
        week_end = week_start + timedelta(days=6)
        
        # Convert transaction dates to date objects for comparison
        week_transactions = []
        for t in transactions:
            t_date = t.date.date() if hasattr(t.date, 'date') else t.date
            if week_start <= t_date <= week_end:
                week_transactions.append(t)
        
        # Aggregate by category for this week
        category_totals = defaultdict(float)
        for t in week_transactions:
            category_totals[t.category.capitalize()] += t.amount
        
        # Convert to list format for bar chart race
        week_data = []
        colors = ['#ff6b35', '#4f8fe8', '#a78bfa', '#ff4d6d', '#f59e0b', '#06b6d4', '#10b981', '#f97316']
        for i, (cat, amount) in enumerate(sorted(category_totals.items(), key=lambda x: x[1], reverse=True)):
            if amount > 0:
                week_data.append({
                    'name': cat,
                    'value': round(amount, 2),
                    'color': colors[i % len(colors)]
                })
        
        weekly_data.append(week_data)
    
    return {
        "status": "success",
        "weekly_data": weekly_data,
        "weeks": 4
    }

@app.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Fetch all transactions for this user
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.user_id
    ).all()
    
    total_spent = sum(t.amount for t in transactions)
    
    # Aggregate by category for Pie Chart
    category_totals = {}
    for t in transactions:
        cat = t.category.capitalize()
        category_totals[cat] = category_totals.get(cat, 0) + t.amount
        
    pie_data = [{"name": cat, "value": round(val, 2)} for cat, val in category_totals.items() if val > 0]
    
    # Sort for the largest categories first
    pie_data = sorted(pie_data, key=lambda x: x["value"], reverse=True)
    
    return {
        "status": "success",
        "total_spent": round(total_spent, 2),
        "pie_data": pie_data,
        "recent_transactions": [
            schemas.TransactionOut.model_validate(t).model_dump() for t in sorted(transactions, key=lambda x: x.date, reverse=True)[:5]
        ]
    }

@app.post("/scan-receipt")
async def scan_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=400, detail="Gemini API Key is not configured. Please add it to your .env file.")
        
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
        
    try:
        content = await file.read()
        
        prompt = """
        Analyze this receipt. Return ONLY a valid JSON object with the following keys:
        - amount: float (total amount paid)
        - merchant: string (name of the store)
        - category: string (one of: Food, Transportation, Entertainment, Utilities, Healthcare, Shopping, Other)
        - date: string (YYYY-MM-DD format if possible, else empty string)
        Make sure the response is strict JSON without markdown blocks or backticks.
        """
        
        from app.ai.providers import get_vision_provider
        vision_provider = get_vision_provider()
        response_text = vision_provider.extract_from_image(prompt, content, file.content_type)
        
        # Sanitize response to just json
        raw_text = response_text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        
        # We could save this to DB immediately or send it back for user confirmation
        # Let's create the transaction
        raw_amount = data.get('amount', 0.0)
        amount_parsed = utils.parse_money(raw_amount)
        amount_value = float(amount_parsed) if amount_parsed is not None else 0.0
        amount_value = abs(amount_value)

        raw_cat = data.get('category', 'uncategorized')
        category_value = str(raw_cat).strip().lower() if raw_cat else "uncategorized"
        if category_value in {"food", "transportation", "entertainment", "utilities", "healthcare", "shopping", "other"}:
            pass
        elif category_value in {"uncategorized", ""}:
            category_value = "uncategorized"
        else:
            category_value = utils.suggest_category(str(data.get("merchant", "")) or "")

        date_val = None
        raw_date = data.get("date", "")
        if raw_date:
            try:
                date_val = pd.to_datetime(raw_date, errors="coerce")
            except Exception:
                date_val = None
        if not date_val or pd.isna(date_val):
            date_val = datetime.utcnow()

        txn = models.Transaction(
            user_id=current_user.user_id,
            amount=amount_value,
            description=f"Receipt: {data.get('merchant', 'Unknown')}",
            category=category_value,
            date=date_val,
            source="receipt"
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)
        
        return {
            "status": "success", 
            "message": f"Extracted receipt from {data.get('merchant', 'Unknown')} for {current_user.currency_symbol}{amount_value}",
            "transaction": txn
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Vision Processing Error: {str(e)}")

# --- CONVERSATIONAL AI & ACTIONS ---

@app.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_ai(
    chat_req: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=400, detail="Gemini API Key is not configured. Please add it to your .env file.")
        
    try:
        # Get richer context (last 20 txns + monthly aggregates)
        recent_txns = db.query(models.Transaction)\
            .filter(models.Transaction.user_id == current_user.user_id)\
            .order_by(models.Transaction.date.desc())\
            .limit(20).all()

        # Monthly windows
        start_this, end_this = _month_window(0)
        start_last, end_last = _month_window(-1)
        this_month_txns = db.query(models.Transaction).filter(
            models.Transaction.user_id == current_user.user_id,
            models.Transaction.date >= start_this,
            models.Transaction.date < end_this
        ).all()
        last_month_txns = db.query(models.Transaction).filter(
            models.Transaction.user_id == current_user.user_id,
            models.Transaction.date >= start_last,
            models.Transaction.date < end_last
        ).all()

        def agg(txns):
            by_cat = defaultdict(float)
            by_merch = defaultdict(float)
            total = 0.0
            for t in txns:
                total += float(t.amount or 0)
                by_cat[(t.category or "other").lower()] += float(t.amount or 0)
                mkey = utils.normalize_merchant_key(t.description or "")
                by_merch[mkey] += float(t.amount or 0)
            top_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:5]
            top_merch = sorted(by_merch.items(), key=lambda x: x[1], reverse=True)[:5]
            return {
                "total": round(total, 2),
                "top_categories": [{"category": k, "amount": round(v, 2)} for k, v in top_cats],
                "top_merchants": [{"merchant": (k.title() if k and k != "unknown" else "Unknown"), "amount": round(v, 2)} for k, v in top_merch],
            }

        context_obj = {
            "currency": current_user.currency,
            "currency_symbol": current_user.currency_symbol,
            "this_month": {"window": [start_this.date().isoformat(), (end_this - timedelta(days=1)).date().isoformat()], **agg(this_month_txns)},
            "last_month": {"window": [start_last.date().isoformat(), (end_last - timedelta(days=1)).date().isoformat()], **agg(last_month_txns)},
            "recent_transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "date": t.date.strftime('%Y-%m-%d') if t.date else None,
                    "amount": float(t.amount or 0),
                    "category": (t.category or "other").lower(),
                    "description": t.description or ""
                }
                for t in recent_txns
            ],
            "active_goals": [
                {
                    "goal_id": g.goal_id,
                    "goal_type": g.goal_type,
                    "target_amount": float(g.target_amount or 0),
                    "deadline": g.deadline.strftime('%Y-%m-%d') if g.deadline else None,
                    "status": g.status
                }
                for g in db.query(models.BudgetGoal).filter(
                    models.BudgetGoal.user_id == current_user.user_id,
                    models.BudgetGoal.status == "active"
                ).all()
            ]
        }

        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Determine Persona
        txn_context = json.dumps(context_obj, default=str)
        if chat_req.roast_mode:
            system_prompt = f"""
            You are FinMate, an absolutely ruthless, sarcastic, and funny AI financial advisor.
            Your job is to roast the user's spending habits while technically giving sound financial advice. 
            Be punchy, mean (but in a fun way), and use Gen-Z/internet slang where appropriate.
            
            User Context (Recent spending):
            {txn_context}
            """
        else:
            system_prompt = f"""
            You are FinMate, a supportive, intelligent, and highly professional AI financial advisor.
            Provide actionable, empathetic, and clear financial guidance.
            
            User Context (Recent spending):
            {txn_context}
            """
            
        # Tool-action prompt (upgrade assistant from chat -> actions)
        action_prompt = f"""
CONTEXT (JSON, reliable):
{json.dumps(context_obj)}

You can answer normally OR you can trigger one tool action by outputting STRICT JSON.

If you trigger an action, return ONLY JSON (no markdown) in this exact shape:
{{
  "response": "A short, friendly message to the user about what happened and why.",
  "action_type": "create_budget_goal" | "show_transactions" | "recategorize_transactions",
  "action_payload": {{ ... }}
}}

Allowed actions:
1) create_budget_goal
  action_payload: {{
    "goal_type": "savings" | "debt_repayment" | "investment",
    "target_amount": number,
    "deadline": "YYYY-MM-DD"
  }}

2) show_transactions
  action_payload: {{
    "merchant_query": "string",
    "limit": number
  }}

3) recategorize_transactions
  action_payload: {{
    "transaction_ids": [number, ...],
    "category": "food"|"transportation"|"entertainment"|"utilities"|"healthcare"|"shopping"|"housing"|"other"
  }}

Rules:
- Only output JSON when you truly want the backend to perform one of these actions.
- For recategorize: pick transaction_ids from CONTEXT.recent_transactions (typically 1-20 ids).
- Otherwise respond in plain text.
"""
        
        full_prompt = system_prompt + "\n" + action_prompt + "\n\nUser says: " + chat_req.message
        
        response = model.generate_content(full_prompt)
        text = response.text.strip()
        
        # Check if the AI returned Action JSON
        if text.startswith('{') and text.endswith('}'):
            try:
                # Need to strip possible markdown that might wrap it despite instructions
                clean_text = text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_text)
                action_type = data.get("action_type")
                payload = data.get("action_payload") or {}

                if action_type == "create_budget_goal":
                    goal_type = str(payload.get("goal_type", "savings")).strip()
                    target_amount = float(payload.get("target_amount", 0))
                    deadline_s = str(payload.get("deadline", "")).strip()
                    deadline_dt = pd.to_datetime(deadline_s, errors="coerce")
                    if target_amount <= 0 or deadline_dt is None or pd.isna(deadline_dt):
                        raise ValueError("Invalid goal payload")
                    new_goal = models.BudgetGoal(
                        user_id=current_user.user_id,
                        goal_type=goal_type,
                        target_amount=target_amount,
                        deadline=deadline_dt.to_pydatetime()
                    )
                    db.add(new_goal)
                    db.commit()
                    db.refresh(new_goal)
                    return schemas.ChatResponse(
                        response=data.get("response") or f"Goal created: {goal_type} target {current_user.currency_symbol}{target_amount:.0f} by {deadline_dt.date().isoformat()}.",
                        action_type="create_budget_goal",
                        action_payload={"goal_id": new_goal.goal_id, "goal_type": goal_type, "target_amount": target_amount, "deadline": deadline_dt.date().isoformat()}
                    )

                if action_type == "show_transactions":
                    q = str(payload.get("merchant_query", "")).strip()
                    limit = int(payload.get("limit", 12) or 12)
                    limit = max(1, min(25, limit))
                    if not q:
                        raise ValueError("Missing merchant_query")
                    matches = db.query(models.Transaction).filter(
                        models.Transaction.user_id == current_user.user_id,
                        models.Transaction.description.ilike(f"%{q}%")
                    ).order_by(models.Transaction.date.desc()).limit(limit).all()
                    items = [
                        {"transaction_id": t.transaction_id, "date": t.date.strftime("%Y-%m-%d") if t.date else None, "amount": float(t.amount or 0), "category": (t.category or "other"), "description": t.description}
                        for t in matches
                    ]
                    return schemas.ChatResponse(
                        response=data.get("response") or f"Here are the most recent transactions matching “{q}”.",
                        action_type="show_transactions",
                        action_payload={"merchant_query": q, "transactions": items}
                    )

                if action_type == "recategorize_transactions":
                    ids = payload.get("transaction_ids") or []
                    category = str(payload.get("category", "other")).strip().lower()
                    if not isinstance(ids, list) or not ids:
                        raise ValueError("Missing transaction_ids")
                    updated = 0
                    for tid in ids:
                        txn = db.query(models.Transaction).filter(
                            models.Transaction.user_id == current_user.user_id,
                            models.Transaction.transaction_id == int(tid)
                        ).first()
                        if txn:
                            txn.category = category
                            updated += 1
                    db.commit()
                    return schemas.ChatResponse(
                        response=data.get("response") or f"Updated {updated} transactions to category “{category}”.",
                        action_type="recategorize_transactions",
                        action_payload={"updated": updated, "category": category, "transaction_ids": ids}
                    )

                return schemas.ChatResponse(
                    response=data.get('response', 'Action executed.'),
                    action_type=data.get('action_type', 'none'),
                    action_payload=data.get('action_payload', None)
                )
            except json.JSONDecodeError:
                pass # Fall back to treating it as regular text
            except Exception:
                pass
                
        return schemas.ChatResponse(
            response=text,
            action_type="none",
            action_payload=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")


# --- BUDGET GOALS ENDPOINTS ---

@app.post("/goals", response_model=schemas.BudgetGoalOut)
def create_budget_goal(
    goal: schemas.BudgetGoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Create a new budget goal via shared GoalService"""
    return GoalService(db).create_goal(current_user, goal)

@app.get("/goals", response_model=list[schemas.BudgetGoalOut])
def list_budget_goals(
    status: str = Query(None, description="Filter by state"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """List user's budget goals with optional filtering via shared GoalService"""
    return GoalService(db).list_goals(current_user.user_id, status=status)

@app.put("/goals/{goal_id}", response_model=schemas.BudgetGoalOut)
def update_budget_goal(
    goal_id: int,
    update: schemas.BudgetGoalUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Update a budget goal via shared GoalService"""
    return GoalService(db).update_goal(goal_id, current_user.user_id, update)

@app.delete("/goals/{goal_id}")
def delete_budget_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Delete a budget goal via shared GoalService"""
    return GoalService(db).delete_goal(goal_id, current_user.user_id)


# --- GAMIFICATION ENDPOINTS ---

@app.get("/stats", response_model=schemas.UserStatsOut)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get user's gamification stats"""
    if not current_user.stats:
        stats = models.UserStats(user_id=current_user.user_id)
        db.add(stats)
        db.commit()
        db.refresh(stats)
        return stats
    
    return current_user.stats

@app.get("/achievements", response_model=list[schemas.AchievementOut])
def get_achievements(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get user's unlocked achievements"""
    achievements = db.query(models.Achievement).filter(
        models.Achievement.user_id == current_user.user_id
    ).order_by(models.Achievement.unlocked_at.desc()).all()
    
    return achievements

@app.get("/notifications", response_model=list[schemas.NotificationOut])
def get_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get user's notifications"""
    query = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.user_id
    )
    
    if unread_only:
        query = query.filter(models.Notification.is_read == False)
    
    return query.order_by(models.Notification.created_at.desc()).limit(20).all()

@app.put("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Mark notification as read"""
    notification = db.query(models.Notification).filter(
        models.Notification.notification_id == notification_id,
        models.Notification.user_id == current_user.user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    return {"status": "success"}


# --- AI INSIGHTS ENDPOINTS ---

@app.get("/insights/anomalies")
def get_spending_anomalies(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get AI-detected unusual spending patterns"""
    insight = ai_insights.analyze_spending_anomalies(db, current_user, GEMINI_API_KEY)
    unusual_expenses = ai_insights.detect_unusual_expenses(db, current_user)
    
    return {
        "insight": insight,
        "unusual_expenses": unusual_expenses
    }

@app.get("/insights/weekly-digest")
def get_weekly_digest(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get personalized weekly financial summary"""
    digest = ai_insights.generate_weekly_digest(db, current_user, GEMINI_API_KEY)
    return digest or {"title": "Weekly Summary", "summary": "No data yet", "total_spent": 0}

@app.get("/insights/budget-optimization")
def get_budget_optimization(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get AI-powered budget optimization suggestions"""
    suggestions = ai_insights.suggest_budget_optimization(db, current_user, GEMINI_API_KEY)
    return {"suggestions": suggestions or "Collect more transaction data to get personalized suggestions."}


# --- RECEIPT MANAGEMENT ENDPOINTS ---

@app.post("/receipts/scan-and-confirm")
async def scan_receipt_with_confirmation(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Scan receipt and save for user confirmation before creating transaction"""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=400, detail="Gemini API Key is not configured.")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    
    try:
        content = await file.read()
        
        from app.ai.providers import get_vision_provider
        vision_provider = get_vision_provider()
        
        prompt = """
        Analyze this receipt. Return ONLY a valid JSON object with the following keys:
        - amount: float (total amount paid)
        - merchant: string (name of the store)
        - category: string (one of: Food, Transportation, Entertainment, Utilities, Healthcare, Shopping, Other)
        - date: string (YYYY-MM-DD format if possible, else empty string)
        - description: string (human readable description)
        """
        
        response_text = vision_provider.extract_from_image(prompt, content, file.content_type)
        raw_text = response_text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        
        # Save as pending receipt for confirmation
        pending = models.ReceiptPending(
            user_id=current_user.user_id,
            extracted_data=json.dumps(data),
            status="pending"
        )
        db.add(pending)
        db.commit()
        db.refresh(pending)
        
        return {
            "receipt_id": pending.receipt_id,
            "data": data,
            "status": "pending_confirmation"
        }
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse receipt: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Receipt processing error: {str(e)}")

@app.post("/receipts/{receipt_id}/confirm")
def confirm_receipt(
    receipt_id: int,
    confirm_req: schemas.ReceiptConfirmRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Confirm and create transaction from pending receipt"""
    pending = db.query(models.ReceiptPending).filter(
        models.ReceiptPending.receipt_id == receipt_id,
        models.ReceiptPending.user_id == current_user.user_id
    ).first()
    
    if not pending:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    if confirm_req.confirmed:
        data = json.loads(pending.extracted_data)
        
        # Override with user-provided values if any
        amount = confirm_req.amount or data.get('amount', 0)
        description = confirm_req.description or data.get('description', data.get('merchant', 'Receipt'))
        category = confirm_req.category or data.get('category', 'uncategorized')
        
        # Create transaction
        txn = models.Transaction(
            user_id=current_user.user_id,
            amount=amount,
            description=description,
            category=category.lower(),
            source="receipt"
        )
        db.add(txn)
        
        pending.status = "confirmed"
        db.commit()
        db.refresh(txn)
        
        gamification.check_and_award_achievement(db, current_user, "receipt_scanner")
        
        return {"status": "success", "transaction_id": txn.transaction_id}
    else:
        pending.status = "rejected"
        db.commit()
        return {"status": "success", "message": "Receipt rejected"}


# --- LEADERBOARD & SOCIAL ENDPOINTS ---

@app.get("/leaderboard/savings-rate")
def get_savings_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get top savers (simulated - in production would anonymize)"""
    # Get all users with stats
    all_stats = db.query(models.UserStats).filter(
        models.UserStats.total_xp > 0
    ).order_by(models.UserStats.longest_streak.desc(), models.UserStats.total_xp.desc()).limit(limit).all()
    
    leaderboard = []
    for stat in all_stats:
        leaderboard.append({
            "rank": len(leaderboard) + 1,
            "name": f"Saver #{stat.user_id % 1000:03d}",
            "streak": stat.longest_streak,
            "xp": stat.total_xp
        })
    
    return {"leaderboard": leaderboard}


# --- DEBATE MODE ---

@app.post("/debate/offers", response_model=schemas.OfferAggregateOut)
@limiter.limit("30/minute")
async def debate_offers(
    request: Request,
    req: schemas.OfferQueryIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Search product offers across multiple providers with partial-failure handling.
    Provider implementations are best-effort (demo-friendly).
    """
    cache_key = f"{current_user.user_id}:{req.priority}:{req.max_results}:{(req.location or '').strip().lower()}:{req.query.strip().lower()}"
    cached = _offers_cache.get(cache_key)
    if cached:
        return cached

    providers = default_offer_providers()
    offers: list[schemas.OfferOut] = []
    errors_by_provider: dict[str, str] = {}

    import asyncio

    async def _run(p):
        try:
            return await p.search(
                query=req.query,
                max_results=req.max_results,
                location=req.location,
                timeout_s=4.0,
            )
        except Exception as e:
            # Should not happen if adapter follows contract, but keep API resilient.
            return {"provider": getattr(p, "name", "web"), "offers": [], "error": f"provider_failed:{type(e).__name__}"}

    results = await asyncio.gather(*[_run(p) for p in providers], return_exceptions=False)
    for r in results:
        provider = r.provider if hasattr(r, "provider") else r.get("provider")
        err = r.error if hasattr(r, "error") else r.get("error")
        prov_offers = r.offers if hasattr(r, "offers") else r.get("offers", [])
        if err:
            errors_by_provider[str(provider)] = str(err)
        for o in prov_offers or []:
            offers.append(o)

    recommended = debate.pick_recommended_offer(offers, req.priority)
    out = schemas.OfferAggregateOut(
        query=req.query,
        priority=req.priority,
        offers=offers,
        errors_by_provider=errors_by_provider,
        recommended_offer=recommended,
    )
    _offers_cache.set(cache_key, out)
    return out


@app.post("/debate/run", response_model=schemas.DebateOut)
@limiter.limit("30/minute")
async def debate_run(
    request: Request,
    req: schemas.DebateRunIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    offers_bundle = await debate_offers(
        request,
        schemas.OfferQueryIn(query=req.query, max_results=req.max_results, priority=req.priority, location=req.location),
        db=db,
        current_user=current_user,
    )

    # Lightweight user context (kept short so it stays stable in demos).
    income = current_user.profile.monthly_income if current_user.profile else None
    user_context = f"monthly_income={income}" if income else "monthly_income=unknown"

    return debate.run_debate(
        gemini_api_key=GEMINI_API_KEY,
        query=req.query,
        priority=req.priority,
        offers=offers_bundle.offers,
        user_context=user_context,
    )

# --- ANALYTICS ENHANCEMENTS ---

@app.get("/analytics/enhanced")
def get_enhanced_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get enhanced analytics with trends and insights"""
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.user_id,
        models.Transaction.date >= start_date
    ).all()
    
    summary = utils.generate_spending_summary(transactions)
    health_score = utils.calculate_health_score(
        summary["total"],
        current_user.profile.monthly_income if current_user.profile else None
    )
    
    # Calculate daily average
    if transactions:
        daily_avg = summary["total"] / len(set(t.date.date() if t.date else None for t in transactions if t.date))
    else:
        daily_avg = 0
    
    return {
        "summary": summary,
        "health_score": health_score,
        "daily_average": round(daily_avg, 2),
        "period_days": days
    }


@app.get("/analytics/overview")
def get_overview_analytics(
    month_offset: int = Query(0, ge=-12, le=0, description="0=current month, -1=last month"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Dashboard-focused analytics bundle:
    - health score
    - spending this month + weekly breakdown (last 4 weeks within window)
    - top 3 takeaways (biggest category, biggest merchant, delta vs last month)
    """
    start, end = _month_window(month_offset)
    txns = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.user_id,
        models.Transaction.date >= start,
        models.Transaction.date < end
    ).all()

    total_spent = float(round(sum(t.amount for t in txns), 2))
    health_score = utils.calculate_health_score(
        total_spent,
        current_user.profile.monthly_income if current_user.profile else None
    )

    # Biggest category
    by_category = defaultdict(float)
    for t in txns:
        if t.category:
            by_category[t.category.lower()] += float(t.amount or 0)
    biggest_category = None
    if by_category:
        cat, amt = max(by_category.items(), key=lambda x: x[1])
        biggest_category = {"category": cat, "amount": round(amt, 2)}

    # Biggest merchant (normalized)
    by_merchant = defaultdict(float)
    for t in txns:
        key = utils.normalize_merchant_key(t.description or "")
        by_merchant[key] += float(t.amount or 0)
    biggest_merchant = None
    if by_merchant:
        mkey, amt = max(by_merchant.items(), key=lambda x: x[1])
        merchant_label = mkey.title() if mkey and mkey != "unknown" else "Unknown Merchant"
        biggest_merchant = {"merchant": merchant_label, "amount": round(amt, 2)}

    # Delta vs last month
    prev_start, prev_end = _month_window(month_offset - 1)
    prev_txns = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.user_id,
        models.Transaction.date >= prev_start,
        models.Transaction.date < prev_end
    ).all()
    prev_total = float(round(sum(t.amount for t in prev_txns), 2))
    delta = round(total_spent - prev_total, 2)
    delta_pct = None
    if prev_total > 0:
        delta_pct = round((delta / prev_total) * 100.0, 1)

    # Weekly totals (up to last 4 weeks within window)
    weekly = []
    cursor = start
    while cursor < end:
        week_end = min(cursor + timedelta(days=7), end)
        week_total = 0.0
        for t in txns:
            if t.date and cursor <= t.date < week_end:
                week_total += float(t.amount or 0)
        weekly.append({
            "start": cursor.date().isoformat(),
            "end": (week_end - timedelta(days=1)).date().isoformat(),
            "total": round(week_total, 2)
        })
        cursor = week_end
    weekly = weekly[-4:]

    return {
        "window": {"start": start.date().isoformat(), "end": (end - timedelta(days=1)).date().isoformat()},
        "total_spent": total_spent,
        "previous_total_spent": prev_total,
        "delta_vs_last_month": {"amount": delta, "percent": delta_pct},
        "health_score": health_score,
        "takeaways": {
            "biggest_category": biggest_category,
            "biggest_merchant": biggest_merchant
        },
        "weekly": weekly,
        "by_category": {k: round(v, 2) for k, v in by_category.items()}
    }

from app.api.v1.analytics import get_financial_overview as _get_fin_overview

@app.get("/analytics/financial-overview")
def get_financial_overview_endpoint(
    month_offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Deterministic financial overview including spending analytics, monthly comparison, and signals."""
    return _get_fin_overview(month_offset=month_offset, db=db, current_user=current_user)

@app.get("/analytics/trends")
def get_spending_trends(
    category: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get spending trends over time"""
    from datetime import timedelta
    from collections import defaultdict
    
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    query = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.user_id,
        models.Transaction.date >= ninety_days_ago
    )
    
    if category:
        query = query.filter(models.Transaction.category == category)
    
    transactions = query.all()
    
    # Group by week
    weekly_data = defaultdict(float)
    for t in transactions:
        if t.date:
            week_key = t.date.strftime('%Y-W%U')
            weekly_data[week_key] += t.amount
    
    trends = [
        {"week": week, "amount": round(amount, 2)}
        for week, amount in sorted(weekly_data.items())
    ]
    
    return {"trends": trends[:13]}  # 13 weeks ~3 months


def _detect_subscription_candidates(db: Session, current_user: models.User):
    """
    Heuristic recurring-merchant detector optimized for demo reliability.
    """
    from datetime import timedelta
    import statistics

    lookback_days = 180
    start_date = datetime.utcnow() - timedelta(days=lookback_days)
    txns = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.user_id,
        models.Transaction.date >= start_date
    ).order_by(models.Transaction.date.asc()).all()

    by_merchant = defaultdict(list)
    for t in txns:
        key = utils.normalize_merchant_key(t.description)
        by_merchant[key].append(t)

    candidates = []
    for merchant_key, items in by_merchant.items():
        if len(items) < 2:
            continue

        dates = sorted([i.date for i in items if i.date])
        if len(dates) < 2:
            continue

        diffs = []
        for a, b in zip(dates, dates[1:]):
            diffs.append((b - a).days)
        diffs = [d for d in diffs if 1 <= d <= 90]
        if not diffs:
            continue

        median_diff = int(statistics.median(diffs))
        # subscription-ish: roughly monthly cadence
        if not (20 <= median_diff <= 45):
            continue

        avg_amount = round(sum(i.amount for i in items) / len(items), 2)
        last_seen_at = max(dates)
        occurrences = len(items)

        closeness = max(0.0, 1.0 - (abs(median_diff - 30) / 15.0))  # 30±15 -> 1..0
        confidence = 0.5 + min(0.3, max(0.0, (occurrences - 2) * 0.1)) + (0.2 * closeness)
        confidence = max(0.0, min(1.0, confidence))

        candidate_id = utils.make_candidate_id(current_user.user_id, merchant_key)
        merchant = merchant_key.title() if merchant_key != "unknown" else "Unknown Merchant"

        candidates.append({
            "candidate_id": candidate_id,
            "merchant": merchant,
            "avg_amount": float(avg_amount),
            "estimated_monthly_cost": float(avg_amount),
            "occurrences": int(occurrences),
            "interval_days": int(median_diff),
            "last_seen_at": last_seen_at,
            "confidence": float(round(confidence, 2))
        })

    # Sort: highest monthly cost first, then confidence
    candidates.sort(key=lambda c: (c["estimated_monthly_cost"], c["confidence"]), reverse=True)
    return candidates[:12]


@app.get("/subscriptions/detect", response_model=schemas.SubscriptionDetectResponse)
def detect_subscriptions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    raise HTTPException(status_code=410, detail="Subscription creep feature removed.")


@app.post("/subscriptions/{candidate_id}/action", response_model=schemas.SubscriptionActionResponse)
def subscription_action(
    candidate_id: str,
    req: schemas.SubscriptionActionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    raise HTTPException(status_code=410, detail="Subscription creep feature removed.")


@app.get("/subscriptions/suspects", response_model=list[schemas.SubscriptionSuspectOut])
def list_subscription_suspects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Lightweight, suggestion-only subscription suspects list.
    Uses heuristic detection and overlays any stored keep/removed decisions.
    """
    candidates = _detect_subscription_candidates(db, current_user)

    # Load existing decisions for this user
    decisions = db.query(models.SubscriptionDecision).filter(
        models.SubscriptionDecision.user_id == current_user.user_id
    ).all()
    by_candidate = {d.candidate_id: d for d in decisions}

    result: list[schemas.SubscriptionSuspectOut] = []
    for c in candidates:
        decision_obj = by_candidate.get(c["candidate_id"])
        decision: str | None = None
        if decision_obj:
            # Map internal actions to simple keep/removed flags for UI
            if decision_obj.action == "keep":
                decision = "keep"
            elif decision_obj.action in {"cancel", "removed"}:
                decision = "removed"
        result.append(
            schemas.SubscriptionSuspectOut(
                candidate_id=c["candidate_id"],
                merchant=c["merchant"],
                avg_amount=c["avg_amount"],
                estimated_monthly_cost=c["estimated_monthly_cost"],
                occurrences=c["occurrences"],
                interval_days=c["interval_days"],
                last_seen_at=c["last_seen_at"],
                confidence=c["confidence"],
                decision=decision,
            )
        )
    return result


@app.post("/subscriptions/suspects/{candidate_id}/decision")
def set_subscription_suspect_decision(
    candidate_id: str,
    req: schemas.SubscriptionSuspectDecisionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Store a simple keep/removed decision for a subscription suspect.
    """
    # Find an example candidate to copy metadata from (best-effort)
    candidates = _detect_subscription_candidates(db, current_user)
    meta = next((c for c in candidates if c["candidate_id"] == candidate_id), None)

    action_internal = "keep" if req.decision == "keep" else "cancel"

    decision = (
        db.query(models.SubscriptionDecision)
        .filter(
            models.SubscriptionDecision.user_id == current_user.user_id,
            models.SubscriptionDecision.candidate_id == candidate_id,
        )
        .first()
    )
    if not decision:
        decision = models.SubscriptionDecision(
            user_id=current_user.user_id,
            candidate_id=candidate_id,
            merchant=meta["merchant"] if meta else "",
            avg_amount=meta["avg_amount"] if meta else 0.0,
            interval_days=meta["interval_days"] if meta else 30,
            occurrences=meta["occurrences"] if meta else 0,
            last_seen_at=meta["last_seen_at"] if meta else None,
            action=action_internal,
        )
        db.add(decision)
    else:
        decision.action = action_internal
    db.commit()
    return {"status": "success", "decision": req.decision}

