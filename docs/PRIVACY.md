# FinMate 2.0 — Privacy Architecture & Data Protection Controls

## 1. Privacy Principles & Commitment
FinMate 2.0 treats user financial data with strict zero-trust confidentiality. Personal financial records (transactions, bank statements, OCR scans, account balances) belong solely to the user. FinMate operates under three core privacy mandates:
1. **Zero Secret Exposure**: Passwords, API keys, JWT session tokens, and database credentials are never transmitted in logs, analytics, or external AI calls.
2. **User Data Sovereignty**: Users retain complete rights to export their full financial profile or permanently delete their account and all associated records.
3. **Transparent AI Boundaries**: Users are explicitly informed regarding what data is shared with external AI providers and have verifiable guarantees regarding data isolation.

---

## 2. Privacy & Data Rights Endpoints

FinMate 2.0 provides compliant data rights endpoints accessible to authenticated users:

### 2.1 Complete Data Export (Right to Portability)
- **Endpoint**: `GET /api/v1/user/export-data`
- **Authentication**: Required (`Bearer <JWT>`)
- **Payload**: Full structured JSON bundle containing:
  - Profile metadata (`user_id`, `name`, `email`, `created_at`, `preferences`)
  - All historical transactions (`id`, `date`, `amount`, `category`, `description`)
  - All active and completed financial goals (`id`, `title`, `target_amount`, `current_amount`, `deadline`)
  - Configured budgets
  - Subscription decisions and review logs
- **Security Guarantee**: The exported bundle strictly excludes `hashed_password`, session tokens, or API secrets.

### 2.2 Account & Data Erasure (Right to Be Forgotten)
- **Endpoint**: `DELETE /api/v1/user/account`
- **Authentication**: Required (`Bearer <JWT>`)
- **Behavior**: Permanently deletes the user record and cascades immediate hard-deletion across all associated entities:
  - Transactions
  - Goals and goal history
  - Budgets and preferences
  - Subscription decisions
  - AI chat logs
- **Audit Verification**: Verified by automated regression tests; all child records are removed synchronously within a single transaction.

### 2.3 AI Disclosure & Transparency
- **Endpoint**: `GET /api/v1/user/ai-disclosure`
- **Description**: Returns transparent metadata explaining AI integration parameters, data retention policies, and scrubbing controls.

---

## 3. Data Transmission Boundaries to External AI Providers

FinMate 2.0 leverages Google Gemini 1.5 Flash for conversational financial insights and weekly briefings. The following data boundary rules are strictly enforced:

### What Is Sent to External AI Providers:
- **Aggregated Financial Summaries**: Monthly total expenditure, categorical spend percentages, net surplus/deficit.
- **Sanitized Transaction Samples**: Anonymized recent transaction lines (e.g. date, category, sanitized description) stripped of raw personal identifiers.
- **User Prompt Text**: User-submitted chat questions after input validation and prompt injection scrubbing.

### What Is NEVER Sent to External AI Providers:
- ❌ Passwords or hashed credentials
- ❌ Bearer tokens, session cookies, or JWTs
- ❌ Account numbers, routing numbers, or credit card PANs
- ❌ Full name, physical address, or phone numbers
- ❌ Internal database IDs, API keys, or infrastructure connection strings

---

## 4. Encryption & Secret Management
- **At Rest**: Password hashes are stored using standard salted bcrypt algorithms.
- **In Transit**: All API traffic is routed over TLS 1.3 in production environments.
- **Environment Isolation**: API secrets (`GEMINI_API_KEY`, `SECRET_KEY`, `DATABASE_URL`) are read exclusively from environment variables and never checked into source control or exposed to clients.
