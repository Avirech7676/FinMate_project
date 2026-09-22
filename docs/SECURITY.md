# FinMate 2.0 — Security Standards & Cross-User Isolation

## 1. Multi-Tenant Cross-User Isolation
FinMate 2.0 enforces zero-trust data segregation across all API endpoints:
- Every query, mutation, and aggregation filters by `user_id == current_user.user_id`.
- Automated regression suite (`tests/test_cross_user_security.py`) formally verifies that User A can NEVER access or mutate:
  - User B transactions (view, update, delete)
  - User B goals (view, update, delete)
  - User B analytics and spending breakdowns
  - User B forecasting models
  - User B explainable health scores
  - User B purchase simulations
  - User B AI chat sessions and tool executions
  - User B data export bundles (`/api/v1/user/export-data`)

---

## 2. Authentication & Credential Protection
- Passwords are encrypted using bcrypt hashing (`passlib[bcrypt]`). Minimum password length (8 chars) and character complexity (uppercase, lowercase, digit, special character) are strictly validated.
- Session tokens use HMAC-SHA256 (`HS256`) JSON Web Tokens with configurable expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- Passwords, hashes, and session tokens are stripped from all logs and export payloads.

---

## 3. AI Prompt Injection & Leakage Defense
- **Indirect Prompt Injection Defense**: Field sanitization (`AIGuardrails.sanitize_field`) neutralizes jailbreaks hidden inside merchant names, transaction notes, CSV rows, or OCR scans.
- **Direct Attack Refusal**: Payloads attempting to dump system prompts or override instructions are rejected with standard safety refusal templates.
- **Sensitive Token Redaction**: Post-generation regex scanning scrubs any leaked Bearer tokens (`[REDACTED_TOKEN]`) or API keys (`[REDACTED_KEY]`).

---

## 4. API & Network Security
- **Observability Middleware**: Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **CORS Protection**: Restricted to configured origins (`FRONTEND_URL`).
- **Rate Limiting**: Integrated via `slowapi` (`Limiter(key_func=get_remote_address)`) to protect against brute-force attacks and abuse.
