# FinMate 2.0 — Comprehensive Changelog

## [2.0.0] - 2026-09-22 — Master Release

### Phase 0: Repository Audit & Safety Baseline
- Audited full backend, frontend, database, AI integrations, test suites, and public contracts.
- Documented baseline operations in `docs/ARCHITECTURE_AUDIT.md` and `docs/BASELINE.md`.

### Phase 1: Architecture Safety & Compatibility Layer
- Created `backend/app/core/config.py` with centralized, typed environment variables.
- Created `backend/app/core/errors.py` with standardized `AppException` error hierarchy.
- Created `backend/app/core/middleware.py` injecting `X-Request-ID`, execution latency, and security headers.
- Added contract aliases (`POST /import-csv`) alongside legacy endpoints (`POST /upload-csv`).

### Phase 2: Service / Repository Architecture
- Separated database persistence into repository layer (`BaseRepository`, `UserRepository`, `TransactionRepository`, `GoalRepository`, `SubscriptionRepository`).
- Extracted business logic into domain services (`UserService`, `TransactionService`, `GoalService`, `SubscriptionService`).
- Mounted modular API v1 routers (`/api/v1/*`) while preserving all legacy endpoints in `main.py`.

### Phase 3: Transaction Pipeline & Data Quality
- Built unified transaction pipeline in `backend/app/services/transaction_pipeline.py`.
- Enforced SHA-256 fingerprint deduplication based on user, merchant, amount, and date.
- Added safe CSV ingestion with preview and duplicate detection in `csv_service.py`.
- Added Gemini Vision receipt OCR staging in `ocr_service.py`.

### Phase 4: Financial Analytics Engine
- Built categorical spending analytics and month-over-month comparisons in `spending.py`.
- Implemented deterministic `FinancialRuleEngine` for budget deficits, high burn rates, and spending spikes.
- Added `GET /analytics/financial-overview`.

### Phase 5: Anomaly Detection & Forecasting
- Created 2-tier layered anomaly detection in `anomalies.py` (Tier 1: Category IQR, Tier 2: ML Isolation Forest).
- Implemented multi-horizon (7-day, 30-day, 90-day) Holt-Winters exponential smoothing forecasting in `forecasting.py`.
- Added endpoints `GET /api/v1/analytics/anomalies/layered` and `GET /api/v1/analytics/forecast`.

### Phase 6: Cash-Flow & Subscription Intelligence
- Created periodic recurring expense detector in `subscriptions.py`.
- Implemented deterministic cash-flow runway engine in `cashflow.py` with 30-day daily balance trajectories.
- Added endpoints `GET /api/v1/cashflow/projection` and `GET /api/v1/subscriptions/intelligence`.

### Phase 7: Goal Planning & Explainable Health Score
- Built `GoalPacingEngine` in `goals.py` computing ON_TRACK, AT_RISK, BEHIND, and COMPLETED statuses with required periodic savings rates.
- Built `ExplainableHealthScoreEngine` in `health_score.py` scoring 5 weighted dimensions (Savings 25%, Budget 25%, Cash Flow 20%, Goals 15%, Consistency 15%) with educational disclaimers.
- Added endpoints `GET /api/v1/goals/pacing` and `GET /api/v1/analytics/health-score/explainable`.

### Phase 8 & 9: Controlled AI Agent, Context Builder & Guardrails
- Created whitelisted deterministic tool registry in `tool_registry.py` scoped strictly to authenticated user identity.
- Built compact, token-efficient financial state context builder in `context_builder.py`.
- Implemented multi-layer prompt defense in `guardrails.py` (injection detection, token scrubbing, educational disclaimers).
- Upgraded conversational assistant in `financial_agent.py` with explainable advice formatting and graceful offline fallback.

### Phase 10: What-If Financial Simulator
- Built `FinancialSimulatorService` in `simulation_service.py` testing purchase impacts on budgets, cash flow runway, and goals.
- Added `POST /simulation/purchase` with structured verdict (AFFORDABLE, PROCEED_WITH_CAUTION, UNRECOMMENDED).

### Phase 11 & 12: Dashboard UX & Report Generation
- Integrated interactive financial panels into React frontend:
  - `FinancialOverviewPanel.tsx`: Income, expenses, savings rate, explainable health score, and financial timeline.
  - `SimulationPanel.tsx`: Interactive purchase simulator with live impact feedback.
  - `ForecastPanel.tsx`: 7d, 30d, 90d forecasts and model assumptions.
  - `AIAdvisorPanel.tsx`: Guardrailed conversational agent with roast mode toggle.
  - `ReportBriefingPanel.tsx`: Weekly intelligence briefing and printable HTML/PDF report downloads.
- Built `WeeklyBriefingEngine` and `FinancialReportService` in backend.

### Phase 13: Security Hardening & Rate Limiting
- Added enterprise password complexity validation (min 8 chars, uppercase, lowercase, digit, special character).
- Added file upload type and size restrictions.
- Added enterprise security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `X-XSS-Protection`, `Referrer-Policy`).
- Integrated `slowapi` rate limiting across API endpoints.

### Phase 14: Automated Testing & CI/CD
- Expanded test suites across backend and frontend.
- Added GitHub Actions workflow in `.github/workflows/ci.yml`.

### Phase 15: Production Validation & Alembic Migrations
- Initialized Alembic migrations in `backend/migrations/` with automated model inspection and baseline revision `488fba0c2a00_initial_schema.py`.

### Phase 16: Final Hardening, Cross-User Security, ML/AI Evaluation & Performance
- **Cross-User Security Suite**: Developed 7 regression tests in `test_cross_user_security.py` verifying complete data segregation between users across all resources.
- **AI Security & Guardrails Hardening**: Implemented indirect prompt injection sanitization in `guardrails.py` and sensitive token scrubbing (`[REDACTED_KEY]`, `[REDACTED_TOKEN]`).
- **Automated AI Evaluation**: Created 7 evaluation tests verifying zero hallucination, grounding in deterministic numbers, and graceful insufficient-data signaling.
- **ML & Forecasting Evaluation**: Conducted reproducible evaluation against synthetic ground-truth datasets; recorded 100% anomaly recall (0.8333 F1) and outperformance of Holt-Winters vs SMA baselines.
- **Performance Benchmarking**: Executed synthetic load benchmarks against 10K and 100K transaction datasets, added composite indexes on `Transaction(user_id, date)` and `BudgetGoal(user_id)`, and confirmed 0% error rate.
- **External Service Resilience**: Tested and verified system behavior during Gemini downtime/timeouts, external price provider outages, and SMTP server failures.
- **Database Hardening**: Verified clean transaction rollback on integrity violation, session closure via `get_db`, and fresh Alembic upgrade/downgrade.
- **Privacy Controls & GDPR**: Added `GET /api/v1/user/export-data`, `DELETE /api/v1/user/account`, and `GET /api/v1/user/ai-disclosure`.
- **LLM Provider Abstraction**: Introduced `LLMProvider` protocol with `GeminiProvider` and `MockProvider`.
- **Demo Seed Script**: Created `scripts/seed_demo_data.py` generating a full realistic 6-month synthetic financial profile (`demo@finmate.local`).
- **Comprehensive Documentation**: Authored `ML_EVALUATION.md`, `FINANCIAL_SCORING_METHODOLOGY.md`, `AI_EVALUATION.md`, `PRIVACY.md`, and `FINAL_VALIDATION_REPORT.md`.
