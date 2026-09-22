# FinMate 2.0 — Safety Baseline Report (Phase 0)

**Date**: September 22, 2026  
**Environment**: Windows 11, Python 3.14.6, Node v24.18.0, npm 11.16.0  
**Status**: Safety Baseline Established  

---

## 1. Commands Executed & Verification Results

### A. Python Backend Verification
- **Command**: `python -m pytest test_main.py -v` (in `backend/`)
- **Prerequisites Installed**:
  - `pip install google-generativeai slowapi alembic aiosmtplib sentry-sdk`
- **Test Results**:
  ```
  test_main.py::TestAuthentication::test_signup_success PASSED             [  9%]
  test_main.py::TestAuthentication::test_signup_duplicate_email PASSED     [ 18%]
  test_main.py::TestAuthentication::test_signup_weak_password PASSED       [ 27%]
  test_main.py::TestAuthentication::test_login_success PASSED              [ 36%]
  test_main.py::TestAuthentication::test_login_wrong_password PASSED       [ 45%]
  test_main.py::TestTransactions::test_create_transaction PASSED           [ 54%]
  test_main.py::TestTransactions::test_create_transaction_invalid_amount PASSED [ 63%]
  test_main.py::TestTransactions::test_create_transaction_auto_categorization PASSED [ 72%]
  test_main.py::TestBudgetGoals::test_create_budget_goal PASSED            [ 81%]
  test_main.py::TestHealth::test_health_check PASSED                       [ 90%]
  test_main.py::TestHealth::test_root_endpoint PASSED                      [100%]
  ```
  - **Summary**: 11 of 11 functional tests passed!
  - **Teardown Note**: On Windows, fixture teardown attempted `os.remove("test.db")` while SQLite retained an open connection handle, throwing `PermissionError: [WinError 32]`. Explicit engine disposal (`engine.dispose()`) before removal resolves this without affecting test results.

### B. Frontend Compilation Verification
- **Command**: `npm install` (in `frontend/`)
  - **Result**: Successfully installed 377 packages in 49 seconds.
- **Command**: `npm run build` (`tsc -b && vite build`)
  - **Result**: Successfully built in 32.83s.
  - **Artifacts**: `dist/index.html` (0.94 kB), `dist/assets/index-OTN9IR4R.css` (89 kB), `dist/assets/index-BJpFCq8r.js` (914 kB). 0 TypeScript compiler errors.

### C. Frontend Unit Test Verification
- **Command**: `npm test -- --run` (in `frontend/`)
  - **Result**: 10 tests in `Dashboard.test.tsx` encountered `ReferenceError: document is not defined`.
  - **Root Cause**: `vitest` runs in standard Node environment by default. `Dashboard.test.tsx` renders React DOM components via `@testing-library/react`, which requires a browser DOM environment (jsdom/happy-dom).
  - **Fix Planned for Phase 1/Testing Phase**: Install `jsdom` and configure `test: { environment: 'jsdom' }` in `vite.config.ts`.

---

## 2. API Contract & Database Health

- **Authentication Flow**:
  - `POST /signup`: Expects `email`, `password`, `full_name`. Validates password length and structure. Hashes with bcrypt.
  - `POST /login`: OAuth2 password request form (`username`, `password`). Returns `{ access_token, token_type: "bearer" }`.
- **Database Engine**:
  - SQLite with `check_same_thread=False` works properly.
  - PostgreSQL pooling configuration in `database.py` is intact for production deployments.
- **Data Preservation**:
  - SQLite databases `finmate.db` and existing tables are untouched.

---

## 3. Known Issues & Pre-Existing Bugs

1. **`test_main.py` cleanup teardown on Windows**: File-lock issue on `test.db`. Needs `engine.dispose()` before `os.remove()`.
2. **Frontend `Dashboard.test.tsx` environment**: Missing `jsdom` dependency and configuration in `vite.config.ts`.
3. **Pydantic V2 Config Deprecation**: `class Config:` in `schemas.py` triggers warnings on Python 3.14.
4. **Python 3.14 `datetime.utcnow()` warnings**: Deprecation warnings during test runs.
5. **Endpoint naming alias**: `POST /import-csv` should be supported alongside existing `POST /upload-csv`.
