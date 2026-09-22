# FinMate 2.0 — Testing & QA Strategy

## 1. Backend Testing Architecture (Pytest)

The backend test suite contains **66+ automated tests** verifying every functional, mathematical, and security boundary:

```bash
cd backend
python -m pytest tests/ test_main.py -v
```

### Test Suites:
1. **`test_main.py` (43 baseline tests)**: Core application workflows, signup, login, transactions, deduplication, CSV ingestion, OCR mock flow, budget goals, gamification, debate engine, legacy endpoints.
2. **`tests/test_cross_user_security.py` (7 tests)**: Cross-user isolation regression suite. Verifies User A cannot read, modify, or simulate User B's transactions, goals, analytics, forecasts, health score, simulations, AI contexts, or data exports.
3. **`tests/test_ai_security_and_eval.py` (7 tests)**: Direct/indirect prompt injection defense, system prompt extraction refusal, token redaction, deterministic calculation grounding, and missing data disclosure.
4. **`tests/test_ml_evaluation.py` (2 tests)**: Layered anomaly detection evaluation (IQR + Isolation Forest, precision/recall/F1) and Holt-Winters forecasting accuracy against 14-day SMA baselines across 7d, 30d, 90d horizons.
5. **`tests/test_external_resilience.py` (4 tests)**: Verification that core transaction and analytical pipelines operate without degradation when external dependencies fail (Gemini offline/timeout/429, price scrapers down, SMTP server offline).
6. **`tests/test_database_hardening.py` (3 tests)**: Transaction rollback verification upon integrity constraint violations, database session closure verification, and programmatic Alembic migration execution.

---

## 2. Frontend Testing Architecture (Vitest & JSDOM)

The frontend test suite tests component rendering, routing, auth context, and user interfaces:

```bash
cd frontend
npm test
```

- **Runner**: Vitest with `@testing-library/react` and `jsdom`.
- **Production Build**: Verified with `npm run build` compiling with 0 TypeScript errors and generating optimized production bundles.
