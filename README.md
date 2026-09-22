# FinMate 2.0 — AI-Powered Personal Financial Intelligence Platform

FinMate 2.0 is an enterprise-grade personal financial intelligence platform engineered with deterministic analytics, layered anomaly detection, Holt-Winters forecasting, cross-user security isolation, and controlled AI copilots powered by Google Gemini (with pluggable `LLMProvider` architecture).

---

## 🎯 What's New in FinMate 2.0

* **Explainable Health Score**: Transparent 0–100 composite rating broken down into 5 weighted pillars (Savings 25%, Budget 25%, Cash Flow 20%, Goals 15%, Consistency 15%) with mathematical explanations and educational disclaimers.
* **Layered Anomaly Detection**: Hybrid 3-tier pipeline combining deterministic rule heuristics, category-specific Interquartile Range (IQR) filtering, and unsupervised Scikit-Learn Isolation Forests (100% recall on benchmark evaluation).
* **Holt-Winters Forecasting**: Multi-horizon (7-day, 30-day, 90-day) Statsmodels triple exponential smoothing with weekly seasonality tracking (additive trend, additive seasonality, 7-day period), outperforming moving-average baselines.
* **Cash-Flow & Runway Engine**: 30-day forward daily balance projections, fixed vs variable expense decomposition, and cash-shortage early warning.
* **Deterministic "What-If" Purchase Simulator**: Multi-dimensional impact analysis on category budgets, cash reserves, and goal deadlines before large discretionary expenditures.
* **Controlled AI Financial Copilot**: Guardrailed conversational agent backed by deterministic calculations, prompt injection defense, sensitive token scrubbing, and deterministic financial grounding and guarded AI responses.
* **Multi-Provider AI Abstraction**: Clean `LLMProvider` and `VisionProvider` architecture supporting `GeminiProvider`, `GeminiVisionProvider`, and deterministic `MockProvider` / `MockVisionProvider` for testing.
* **Strict Cross-User Isolation**: Zero-trust multi-tenant security ensuring complete data segregation across transactions, goals, analytics, forecasts, and AI sessions.
* **Data Sovereignty & Privacy Controls**: Endpoints for full JSON personal data export, account and data hard erasure, and transparent AI disclosures.
* **Alembic Database Migrations**: Non-destructive schema authority with composite performance indexes (`transactions(user_id, date)` and `budget_goals(user_id)`).
* **Safe Demo Mode & Seeding**: Automated synthetic demo data generator (`scripts/seed_demo_data.py`) with 6 months of realistic transactions, goals, subscriptions, and anomalies.

---

## 🏗️ Architecture & Tech Stack

* **Backend**: FastAPI (Python 3.11/3.14) + SQLAlchemy + Pydantic V2 + Scikit-Learn + Statsmodels
* **AI Engine**: Google Gemini 1.5/2.5 Flash via `LLMProvider` and `VisionProvider` abstractions
* **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS + Lucide Icons
* **Database**: SQLite (local development) / PostgreSQL (production) with Alembic migrations
* **Security**: JWT (`HS256`), bcrypt password hashing, `slowapi` rate limiting, enterprise security headers

---

## 📦 Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Run database migrations to head
python -m alembic upgrade head

# (Optional) Seed realistic synthetic demo environment
python scripts/seed_demo_data.py
# Demo credentials: demo@finmate.local / DemoMode2026!

# Start FastAPI server
uvicorn main:app --reload --port 8000
```

Backend interactive API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

## 🧪 Testing & Verification

FinMate 2.0 includes an exhaustive test suite covering unit, integration, cross-user isolation, AI guardrails, ML benchmarks, and database rollbacks (74 backend tests + 4 frontend tests = 78 verified passing tests):

```bash
# Run all backend tests (74 verified tests)
cd backend
python -m pytest tests/ test_main.py -v

# Run frontend tests (Vitest + JSDOM: 4 verified tests)
cd frontend
npm test

# Run frontend production build (TypeScript check + Vite bundle: 0 errors)
npm run build
```

---

## 📚 Technical Documentation

* [Architecture Specification](docs/ARCHITECTURE.md)
* [Complete API Reference](docs/API.md)
* [AI Architecture & Guardrails](docs/AI_ARCHITECTURE.md)
* [AI Evaluation & Anti-Injection Benchmarks](docs/AI_EVALUATION.md)
* [Machine Learning & Forecasting Evaluation](docs/ML_EVALUATION.md)
* [Financial Health Scoring Methodology](docs/FINANCIAL_SCORING_METHODOLOGY.md)
* [Privacy Architecture & Data Rights](docs/PRIVACY.md)
* [Security Standards & Cross-User Isolation](docs/SECURITY.md)
* [Testing & QA Strategy](docs/TESTING.md)
* [Database Schema & Migration Guide](docs/DATABASE.md)
* [Production Deployment Guide](docs/DEPLOYMENT.md)
* [Final Validation & Hardening Report](docs/FINAL_VALIDATION_REPORT.md)
* [Comprehensive Changelog](docs/CHANGELOG.md)
* [Flutter Mobile Architecture](docs/FLUTTER_ARCHITECTURE.md)
* [Dart Engineering Guide](docs/DART_ENGINEERING.md)
* [Flutter Concurrency & Multi-Isolate Threading](docs/FLUTTER_CONCURRENCY.md)
* [Flutter Testing Strategy](docs/FLUTTER_TESTING.md)
* [Flutter Deployment Guide](docs/FLUTTER_DEPLOYMENT.md)

---

## 📱 Mobile Application

FinMate 2.0 features an enterprise-grade mobile application (`flutter_app/`) built with Flutter and Dart, serving as an authoritative client to the FastAPI backend.

### Key Capabilities:
* **Architecture & State Management**: Clean Architecture paired with **Flutter Riverpod** (`AsyncNotifier`, family providers, autoDispose) for reactive, immutable state.
* **REST Integration & Resilience**: Centralized **Dio** HTTP client with automatic JWT token injection, structured exception translation into typed failures (`NetworkFailure`, `AuthenticationFailure`, `ValidationFailure`, `ServerFailure`), request cancellation, and configurable timeouts.
* **Offline-First Persistence**: Local SQLite database caching read datasets (Overview, Transactions, Health Score, Forecasts) with a dedicated `offline_sync_queue` ensuring mutations created offline never disappear.
* **Multi-Isolate Concurrency Engine**: Persistent `IsolateWorkerPool` distributing CPU-heavy operations across background Dart isolates using bidirectional `SendPort`/`ReceivePort` communication:
  * **Off-Thread CSV Ingestion**: High-throughput parsing supporting RFC 4180 quotes and escaped commas with streaming 0–100% progress reporting without blocking the UI thread.
  * **Off-Thread Statistical Analysis**: Offloads Mean, Median, Variance, Standard Deviation, and IQR anomaly computations to background worker isolates.
* **Controlled AI Assistant**: Chat interface connecting directly to backend guardrails and the FinMate financial agent with real-time tool execution tracking (*"Analyzing anomalies..."*, *"Checking goal progress..."*) without exposing API keys or secrets on the client.
* **Security & Hardware Enclave**: Authentication credentials securely encrypted using **flutter_secure_storage** (Android Keystore / iOS Keychain). Zero API keys or secrets stored on the client.

```bash
# Run Flutter tests
cd flutter_app
dart test
```

---

## 📄 License
MIT License. Built for personal financial intelligence.

