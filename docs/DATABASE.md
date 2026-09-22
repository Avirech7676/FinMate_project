# FinMate 2.0 — Database Schema & Migration Guide

## 1. Supported Engines
- **Development**: SQLite (`sqlite:///./finmate.db`)
- **Production**: PostgreSQL (`postgresql://user:password@host:port/dbname`) via SQLAlchemy with connection pooling.

---

## 2. Database Migrations (Alembic)
FinMate 2.0 manages schema lifecycle via Alembic.

### Running Migrations
```bash
# In backend/
# Upgrade database to latest revision
python -m alembic upgrade head

# Generate a new migration revision
python -m alembic revision --autogenerate -m "describe_changes"

# Roll back by 1 revision
python -m alembic downgrade -1
```

---

## 3. Schema Optimization & Performance Indexes

To ensure sub-100ms response times at scale (verified up to 100K transactions):
- **`ix_transactions_user_date`**: Composite index on `(user_id, date DESC)` for instant transaction history and range-based analytics.
- **`ix_budget_goals_user`**: Index on `(user_id)` for rapid goal lookups and pacing calculations.
- **`ix_subscription_decisions_user`**: Index on `(user_id)` for subscription review workflows.

---

## 4. Integrity & Rollback Guarantees
- All mutative database operations (e.g. account deletion cascade, CSV bulk transaction commits) execute inside explicit transactions.
- Automated rollback tests (`tests/test_database_hardening.py`) confirm that failing database operations trigger clean rollbacks without leaving partial records or locking SQLite/PostgreSQL sessions.
- Connection sessions are deterministically yielded and closed via the FastAPI `get_db` dependency.

---

## 5. Entity Reference
1. **`users`**: User identity, hashed passwords, currency, and preferences JSON.
2. **`financial_profiles`**: Employment, monthly income, risk tolerance.
3. **`transactions`**: Amount, date, category, source, description, indexed by user.
4. **`budget_goals`**: Goal targets, deadlines, current progress, status.
5. **`subscription_decisions`**: Candidate recurring expenses, cadence, user review status.
6. **`receipts_pending`**: OCR extraction buffer prior to confirmation.
7. **`user_stats`, `achievements`, `notifications`**: Gamification and streak counters.
