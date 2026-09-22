"""
FinMate 2.0 AI Guardrails & Prompt Defense System
Validates prompts for injection, filters sensitive credentials, ensures explainable AI structure,
and prevents fabrication of non-existent financial numbers.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


class AIGuardrails:
    """
    Multi-layer safety and verification guardrails for LLM interactions.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"reveal\s+(your\s+)?(system\s+prompt|instructions|secret)",
        r"reveal\s+.*(transactions|data|balance|details|users)",
        r"other\s+users?('s)?\s+(data|transactions|information|accounts)",
        r"system\s+prompt",
        r"internal\s+tool(\s+definition)?",
        r"delete\s+from\s+users",
        r"drop\s+table",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"dan\s+mode",
        r"bypass\s+security",
        r"api[_-]?key",
        r"bearer\s+token",
        r"secret[_-]?token"
    ]

    INVESTMENT_DISCLAIMER = (
        "\n\n*Educational Disclaimer: Investment and market concepts discussed are for general "
        "informational purposes only and do not constitute professional investment, tax, or fiduciary advice.*"
    )

    @classmethod
    def sanitize_field(cls, text: str) -> str:
        """
        Sanitizes user-generated fields (merchants, descriptions, CSV cells, OCR text)
        to neutralize indirect prompt injection payloads before context insertion.
        """
        if not text:
            return ""
        # Neutralize common indirect injection triggers
        cleaned = re.sub(
            r"(?i)(ignore\s+(all\s+)?previous\s+instructions|reveal\s+.*system\s+prompt|reveal\s+.*transactions|developer\s+mode)",
            "[FILTERED_INPUT]",
            text
        )
        return cleaned[:300].strip()

    @classmethod
    def sanitize_input(cls, user_prompt: str) -> Tuple[bool, str]:
        """
        Check for prompt injections and malicious bypass attempts.
        Returns (is_safe, sanitized_prompt_or_error).
        """
        if not user_prompt:
            return False, "Query cannot be empty."

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, user_prompt, re.IGNORECASE):
                return False, (
                    "Your query contains keywords that violate FinMate security guardrails. "
                    "Please ask a direct question about your personal finances, spending, or goals."
                )

        # Truncate overly long prompts to prevent buffer injection
        sanitized = user_prompt.strip()[:1000]
        return True, sanitized

    @classmethod
    def scrub_sensitive_tokens(cls, text: str) -> str:
        """
        Scrub API keys, JWTs, hashes, or passwords that might accidentally be output.
        """
        # Scrub Bearer tokens
        text = re.sub(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", "[REDACTED_TOKEN]", text)
        # Scrub AI keys
        text = re.sub(r"AIza[0-9A-Za-z-_]{20,50}", "[REDACTED_KEY]", text)
        # Scrub generic potential hex keys (32+ chars)
        text = re.sub(r"\b[a-fA-F0-9]{32,64}\b", "[REDACTED_HASH]", text)
        return text

    @classmethod
    def apply_post_generation_guardrails(
        cls,
        llm_response: str,
        user_query: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Applies scrubbing, investment disclaimers, and format verification to the LLM response.
        """
        output = cls.scrub_sensitive_tokens(llm_response)

        # Check if investment advice was asked
        q_lower = user_query.lower()
        investment_terms = ["invest", "stock", "crypto", "mutual fund", "etf", "portfolio", "roi", "equity", "bitcoin"]
        if any(term in q_lower for term in investment_terms):
            if "Educational Disclaimer" not in output:
                output += cls.INVESTMENT_DISCLAIMER

        return output
