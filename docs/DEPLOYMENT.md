# FinMate 2.0 — Production Deployment Guide

## Architecture Overview
- **Frontend**: React 19 SPA built with Vite and Tailwind CSS.
- **Backend**: FastAPI ASGI application running with Uvicorn / Gunicorn.
- **Database**: PostgreSQL with connection pooling and Alembic schema management.
- **AI Intelligence**: Google Gemini 1.5 Flash API with deterministic offline fallbacks.

---

## 1. Environment Configuration

### Backend `.env`
```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=generate-a-secure-random-64-character-key
DATABASE_URL=postgresql://finmate_user:dbpassword@postgres-host:5432/finmate_prod
FRONTEND_URL=https://finmate.yourdomain.com
GEMINI_API_KEY=your-production-gemini-api-key
MAIL_USERNAME=notifications@yourdomain.com
MAIL_PASSWORD=your-smtp-password
MAIL_FROM=notifications@yourdomain.com
MAIL_PORT=587
MAIL_SERVER=smtp.sendgrid.net
```

### Frontend `.env`
```env
VITE_API_URL=https://api.finmate.yourdomain.com
```

---

## 2. Database Provisioning & Migrations
```bash
# Apply migrations to production PostgreSQL database
cd backend
python -m alembic upgrade head

# (Optional) Seed realistic synthetic demo environment for staging
python scripts/seed_demo_data.py
```

---

## 3. Backend Deployment (Docker / VPS / Render / Heroku)
Run using Uvicorn with standard workers:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers
```

Or with Docker:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## 4. Frontend Deployment (Vercel / Netlify / Cloudflare Pages)
```bash
cd frontend
npm ci
npm run build
# Publish the dist/ folder to static hosting
```

---

## 5. Health Check & Observability Verification
- Ping `GET /health` -> `{"status": "ok"}`
- Ping `GET /` -> `{"message": "Welcome to FinMate API"}`
- Ping `GET /api/v1/user/ai-disclosure` -> Returns AI privacy disclosure metadata.
- Verify security headers in responses: `X-Request-ID`, `X-Process-Time`, `Strict-Transport-Security`, and `X-Frame-Options: DENY`.
