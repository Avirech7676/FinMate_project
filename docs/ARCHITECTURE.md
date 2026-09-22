# FinMate 2.0 — Architecture Specification

## 1. Architectural Philosophy
FinMate 2.0 evolves from an AI-augmented tracker into a full-scale **Personal Financial Intelligence Platform**. The architecture adheres to four core tenets:
1. **Extend > Replace**: All existing APIs, schemas, and user workflows remain 100% operational.
2. **Deterministic Calculations > LLM Calculations**: Mathematical operations, financial ratios, run-rate forecasts, and threshold triggers are computed strictly via deterministic engines before passing summarized insights to the LLM.
3. **Resilience & Graceful Degradation**: External API failures (Gemini, e-commerce providers, SMTP) never crash core transactional and budgeting operations.
4. **Zero-Trust Multi-Tenancy**: All analytical pipelines, database queries, and AI context builders enforce strict authenticated user isolation.

---

## 2. Layered Target Architecture

```
Client (Web / Mobile SPA)
       │
       ▼
[Observability & Security Middleware]
  - Request ID (UUID)
  - Latency Tracker
  - Security Headers (nosniff, DENY, HSTS)
  - Rate Limiting (slowapi)
       │
       ▼
[FastAPI Route Handlers] (backend/app/api/ and backend/main.py)
  - Input validation (Pydantic V2)
  - Authentication (OAuth2 Bearer JWT)
  - Privacy controls (/user/export-data, /user/account)
  - Request/Response normalization
       │
       ▼
[Service Layer] (backend/app/services/)
  - TransactionPipelineService
  - CashflowService
  - ForecastingService
  - AnomalyDetectionService
  - SimulationService
  - BriefingService
       │
       ▼
[Financial Intelligence & Analytics Engine] (backend/app/analytics/)
  - 3-Tier Layered Anomaly Detection (Rule heuristics, IQR Category Filtering, Isolation Forest)
  - Statsmodels Holt-Winters Triple Exponential Smoothing (7, 30, 90 day horizons)
  - Cash flow projection & subscription periodicity
  - 5-Pillar Explainable Health Score Engine
       │
       ▼
[AI Layer] (backend/app/ai/)
  - Context Builder (compact user profile + metrics)
  - Prompt Manager & Guardrails (injection defense, token scrubbing)
  - Controlled Tool Registry (validated limits: limit 1-50, days 1-365)
  - Pluggable AI Provider Abstractions:
      ├─ LLMProvider: GeminiProvider (Production) / MockProvider (Testing)
      └─ VisionProvider: GeminiVisionProvider (Production) / MockVisionProvider (Testing)
       │
       ▼
[Repository Layer] (backend/app/repositories/)
  - UserRepository, TransactionRepository, GoalRepository, SubscriptionRepository
       │
       ▼
[Data Layer] (backend/database.py & models.py)
  - SQLite (Development) / PostgreSQL (Production) via SQLAlchemy
  - Alembic schema authority with composite indexes:
      ├─ transactions(user_id, date) [ix_transactions_user_date]
      └─ budget_goals(user_id) [ix_budget_goals_user]
```

---

## 3. Communication Contracts
- All backend routes deliver responses in standardized schemas.
- Error payloads follow the uniform envelope:
  ```json
  {
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable explanation",
      "request_id": "uuid"
    }
  }
  ```
- Public legacy endpoints are preserved indefinitely or aliased with exact backwards compatibility.
