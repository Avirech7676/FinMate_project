# FinMate 2.0 — AI Architecture & Guardrails

## 1. Principles of AI Financial Intelligence
1. **Never Calculate with the LLM**: All numerical aggregations, monthly totals, category percentages, run-rates, forecasts, and health scores are computed deterministically in Python. The LLM acts solely as an interpreter, explainer, and natural-language interface.
2. **Context Minimization**: Only the authenticated user's summary metrics and recent window of transactions are provided to the model. Raw database dumps are never fed into prompts.
3. **Graceful Fallback & Pluggable Providers**: Uses an `LLMProvider` abstraction (`GeminiProvider` for live environments and `MockProvider` for deterministic offline testing). If Gemini is unreachable or exhausts quotas, rule-based fallback responses are returned smoothly.
4. **Zero-Tolerance Hallucination Policy**: If data for requested categories or timeframes does not exist, the agent declares insufficient data rather than inventing estimates.

---

## 2. Guardrails & Safety Architecture

```
User Query / Transaction Ingestion
       │
       ▼
[AIGuardrails: sanitize_field / validate_input]
  - Indirect prompt injection filter (regex patterns)
  - Instruction override defense ("ignore previous instructions")
  - System prompt extraction defense
       │
       ▼
[AIContextBuilder: build_compact_context]
  - Strict user-id isolation
  - Sanitized transaction descriptions
  - Pre-aggregated deterministic metrics
       │
       ▼
[LLMProvider: generate_reply]
  - GeminiProvider / MockProvider
  - Temperature: 0.2 (deterministic, low variance)
       │
       ▼
[AIGuardrails: scrub_sensitive_output]
  - Redaction of Bearer tokens ([REDACTED_TOKEN])
  - Redaction of API keys ([REDACTED_KEY])
  - Redaction of credential patterns
       │
       ▼
Client Response Envelope
```

---

## 3. Tool Execution Registry
When the AI copilot triggers an action (such as creating a budget goal or querying an anomaly):
- Only tools in the whitelisted `FinancialToolRegistry` may execute.
- All tools require a validated `user_id` injected from the authenticated session context; LLM parameters cannot target another user's records.
- All actions are logged and verifiable.
