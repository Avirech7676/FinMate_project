# FinMate 2.0 — Complete API Reference & Public Contracts

All legacy endpoints remain 100% backward compatible. New capabilities are accessible both at root aliases and structured `/api/v1/*` endpoints.

## 1. Authentication & Users
- `POST /signup`: Registers new user with enterprise password validation.
  - Body: `{ email, password, full_name }`
  - Response: `UserOut`
- `POST /login`: OAuth2 password flow.
  - Body: `username`, `password` (Form URL-encoded)
  - Response: `{ access_token, token_type: "bearer" }`
- `GET /me`: Current user session profile.
  - Headers: `Authorization: Bearer <token>`
  - Response: `UserOut`

---

## 2. Transactions & Ingestion
- `POST /transactions`: Manual transaction entry with deduplication and auto-categorization.
  - Body: `{ amount, category, date, description, source }`
- `GET /transactions`: Retrieve transaction history.
  - Query: `limit`, `offset`, `search`, `category`
- `PUT /transactions/{id}`: Modify transaction.
- `DELETE /transactions/{id}`: Delete transaction.
- `POST /upload-csv` & `POST /import-csv`: Bank/credit-card CSV import.
  - Features: Automatic delimiter sniffing, header matching, AI normalization with graceful fallback to deterministic parsing.
- `POST /upload-csv/preview`: Pre-flight header detection and sample row extraction.
- `POST /scan-receipt`: Gemini Vision direct receipt extraction into transaction.
- `POST /receipts/scan-and-confirm`: Staged receipt scanning into `ReceiptPending` table.
- `POST /receipts/{id}/confirm`: Confirm or edit pending receipt to active transaction.

---

## 3. Goals & Gamification
- `POST /goals`: Create budget goal.
- `GET /goals`: List user goals.
- `GET /api/v1/goals/pacing`: Pacing calculations (ON_TRACK, AT_RISK, BEHIND, COMPLETED) with required savings rates.
- `GET /api/v1/goals/{id}/pacing`: Pacing metrics for a specific goal.
- `PUT /goals/{id}`: Update goal.
- `DELETE /goals/{id}`: Delete goal.
- `GET /stats`: User XP, streaks, total spend metrics.
- `GET /achievements`: List unlocked badges.
- `GET /leaderboard/savings-rate`: Peer savings benchmark.

---

## 4. Financial Intelligence, Forecasting & Simulator
- `GET /api/v1/analytics/financial-overview`: Month-over-month comparisons and rule signals.
- `GET /api/v1/analytics/anomalies/layered`: 3-tier anomaly detection (Rule heuristics + Category IQR + Unsupervised Isolation Forest).
- `GET /api/v1/analytics/forecast`: 7-day, 30-day, 90-day Statsmodels Holt-Winters exponential smoothing forecast.
- `GET /api/v1/analytics/health-score/explainable`: 5-factor weighted health score with component breakdown and disclaimers.
- `GET /api/v1/cashflow/projection`: 30-day daily balance trajectory, fixed vs variable obligations, and runway risk status.
- `POST /simulation/purchase` & `POST /api/v1/simulation/purchase`:
  - Body: `{ purchase_amount, purchase_category, description, purchase_date }`
  - Response: Detailed budget impact, cash-flow impact, goal impact, risk level, and verdict (`AFFORDABLE`, `PROCEED_WITH_CAUTION`, `UNRECOMMENDED`).

---

## 5. Controlled AI Agent & Tools
- `POST /api/v1/ai/chat`: Guardrailed conversational agent grounded in deterministic financial state.
  - Body: `{ message, roast_mode }`
  - Response: `{ reply, action, is_fallback }`
- `GET /api/v1/ai/tools`: List whitelisted financial tools.
- `POST /api/v1/ai/tools/execute`: Execute a deterministic tool directly for the authenticated user.
- `POST /chat`: Conversational AI with action execution (create budget goal, recategorize transactions, show transactions).

---

## 6. Reports & Weekly Briefing
- `GET /api/v1/analytics/briefing/weekly`: Deterministic 7-day briefing on what changed, top categories, and actionable suggestions.
- `GET /api/v1/analytics/report/summary`: JSON structure of complete financial intelligence report.
- `GET /api/v1/analytics/report/download`: Sanitized, printable HTML/PDF report document.

---

## 7. Subscriptions & Price Debate
- `GET /subscriptions/detect`: Candidate recurring charges.
- `GET /subscriptions/suspects`: Suspect recurring charges list.
- `POST /subscriptions/suspects/{candidate_id}/decision`: User decision (`keep` or `cancel`).
- `POST /debate/offers`: Multi-provider price scraper.
- `POST /debate/run`: Multi-agent purchase debate.

---

## 8. Privacy & Data Rights Controls
- `GET /api/v1/user/export-data`: Full structured JSON export of all transactions, budgets, goals, and profile data (excluding passwords/tokens).
- `DELETE /api/v1/user/account`: Permanent account erasure cascading across transactions, goals, preferences, decisions, and chat records.
- `GET /api/v1/user/ai-disclosure`: Transparent AI model metadata, boundary disclosures, and privacy policies.
