"""
FinMate 2.0 Financial AI Agent
Controlled conversational financial intelligence agent using deterministic context,
whitelisted tools, explainable reasoning structure, and safety guardrails.
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import google.generativeai as genai

import models
from app.core.config import settings
from app.ai.context_builder import AIContextBuilder
from app.ai.guardrails import AIGuardrails

logger = logging.getLogger("finmate.ai.agent")


class FinancialAgent:
    """
    Production-grade AI Financial Agent coordinating deterministic tools, context builder,
    Gemini LLM inference, and safety guardrails.
    """

    SYSTEM_PROMPT = """
You are FinMate 2.0, an elite personal financial intelligence platform assistant.
You operate on strict deterministic principles:
1. All financial numbers, totals, percentages, and dates must be sourced exclusively from the provided USER CONTEXT JSON.
2. Never hallucinate, calculate, or fabricate imaginary balances, market returns, or transactions.
3. If information is missing from the context, clearly inform the user rather than guessing.
4. Provide structured, explainable financial recommendations using this format when giving actionable advice:
   - Recommendation: Clear, specific action
   - Reason: Why this action is beneficial
   - Evidence: Exact numbers/percentages from user context
5. Maintain a professional, highly supportive, and objective financial tone unless roast mode is requested.
"""

    ROAST_PROMPT = """
You are FinMate 2.0 (Roast Mode), a ruthlessly funny, sarcastic AI financial advisor.
Roast the user's spending habits using the EXACT numbers in the context. 
Keep it humorous, punchy, and grounded in truth—never invent false transactions.
"""

    @classmethod
    def execute(
        cls,
        db: Session,
        user: models.User,
        user_query: str,
        roast_mode: bool = False
    ) -> Dict[str, Any]:
        # 1. Sanitize user query against injection attacks
        is_safe, sanitized_or_error = AIGuardrails.sanitize_input(user_query)
        if not is_safe:
            return {
                "reply": sanitized_or_error,
                "action": None,
                "is_fallback": True
            }

        # 2. Build scoped compact context
        context = AIContextBuilder.build_compact_context(db, user, user_query=sanitized_or_error)
        context_json = json.dumps(context, indent=2, default=str)

        from app.ai.providers import get_llm_provider

        try:
            provider = get_llm_provider()
            persona = cls.ROAST_PROMPT if roast_mode else cls.SYSTEM_PROMPT
            full_prompt = (
                f"{persona}\n\n"
                f"### USER FINANCIAL CONTEXT (DETERMINISTIC DATA):\n{context_json}\n\n"
                f"### USER QUERY:\n{sanitized_or_error}\n\n"
                f"Provide your answer grounded entirely in the above context."
            )

            raw_text = provider.generate(full_prompt)
            if not raw_text:
                return cls._deterministic_fallback(context, sanitized_or_error, roast_mode)

            # 4. Apply post-generation safety guardrails
            safe_text = AIGuardrails.apply_post_generation_guardrails(
                raw_text,
                user_query=sanitized_or_error,
                context=context
            )

            return {
                "reply": safe_text,
                "action": None,
                "is_fallback": False
            }

        except Exception as e:
            logger.warning("LLM Provider call failed, activating graceful deterministic fallback: %s", str(e))
            return cls._deterministic_fallback(context, sanitized_or_error, roast_mode)

    @classmethod
    def _deterministic_fallback(
        cls,
        context: Dict[str, Any],
        query: str,
        roast_mode: bool
    ) -> Dict[str, Any]:
        """
        Deterministic, explainable rule-based fallback response when AI is unreachable.
        """
        budget = context.get("budget", {})
        spending = context.get("spending_30d", {})
        currency_sym = context.get("currency_symbol", "₹")
        spent = spending.get("total_spent", 0.0)
        budget_limit = budget.get("monthly_budget", 0.0)

        if roast_mode:
            reply = (
                f"🔥 You've burned through {currency_sym}{spent:,.2f} in the past 30 days! "
                f"Budget: {currency_sym}{budget_limit:,.2f}. "
                f"Maybe it's time to close the shopping apps before your wallet goes on strike."
            )
        else:
            reply = (
                f"FinMate Financial Summary:\n"
                f"- Past 30-Day Spending: {currency_sym}{spent:,.2f}\n"
                f"- Monthly Budget Limit: {currency_sym}{budget_limit:,.2f}\n"
                f"- Budget Utilization: {budget.get('utilization_pct', 0)}%\n\n"
                f"Recommendation: Keep discretionary spending steady to preserve monthly liquidity."
            )

        reply = AIGuardrails.apply_post_generation_guardrails(reply, query, context)
        return {
            "reply": reply,
            "action": None,
            "is_fallback": True
        }
