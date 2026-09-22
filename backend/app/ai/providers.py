"""
FinMate 2.0 AI Provider Abstraction Layer
Provides a uniform interface for LLM inference with GeminiProvider and MockProvider.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from app.core.config import settings

logger = logging.getLogger("finmate.ai.providers")


class LLMProvider(ABC):
    """Abstract Base Class for LLM inference providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text response from the given prompt."""
        pass


class GeminiProvider(LLMProvider):
    """Production provider using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self._configured = False

    def _configure(self):
        if not self._configured and self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._configured = True

    def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
        
        self._configure()
        import google.generativeai as genai
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        return response.text if response and response.text else ""


class MockProvider(LLMProvider):
    """
    Deterministic mock provider for automated tests and offline simulation.
    Can simulate specific responses, delays, timeouts, or quota errors.
    """

    def __init__(
        self,
        default_response: Optional[str] = None,
        simulate_error: Optional[Exception] = None
    ):
        self.default_response = default_response or "Mock deterministic financial analysis response."
        self.simulate_error = simulate_error
        self.call_history = []

    def set_response(self, response: str):
        self.default_response = response

    def set_error(self, error: Optional[Exception]):
        self.simulate_error = error

    def generate(self, prompt: str, **kwargs) -> str:
        self.call_history.append({"prompt": prompt, "kwargs": kwargs})
        if self.simulate_error:
            raise self.simulate_error
        return self.default_response


_active_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Returns the globally configured or default LLM provider."""
    global _active_provider
    if _active_provider is not None:
        return _active_provider

    if settings.GEMINI_API_KEY:
        _active_provider = GeminiProvider()
    else:
        _active_provider = MockProvider()
    return _active_provider


def set_llm_provider(provider: Optional[LLMProvider]):
    """Overrides the global LLM provider (useful for tests)."""
    global _active_provider
    _active_provider = provider


# --- VISION PROVIDER ABSTRACTION ---

class VisionProvider(ABC):
    """Abstract Base Class for Multimodal / Vision inference providers."""

    @abstractmethod
    def extract_from_image(self, prompt: str, image_bytes: bytes, mime_type: str, **kwargs) -> str:
        """Analyze image with prompt and return text response."""
        pass


class GeminiVisionProvider(VisionProvider):
    """Production Vision provider using Google Gemini."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self._configured = False

    def _configure(self):
        if not self._configured and self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._configured = True

    def extract_from_image(self, prompt: str, image_bytes: bytes, mime_type: str, **kwargs) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
        self._configure()
        import google.generativeai as genai
        model = genai.GenerativeModel(self.model_name)
        image_part = {"mime_type": mime_type, "data": image_bytes}
        response = model.generate_content([prompt, image_part])
        return response.text if response and response.text else ""


class MockVisionProvider(VisionProvider):
    """Deterministic mock vision provider for testing and offline execution."""

    def __init__(self, default_response: Optional[str] = None):
        import json
        self.default_response = default_response or json.dumps({
            "merchant": "Mock Store",
            "total": 42.50,
            "amount": 42.50,
            "category": "food",
            "date": "2026-03-15",
            "tax": 3.50,
            "items": [{"name": "Item 1", "price": 42.50}],
            "payment_method": "Visa",
            "confidence": 0.95,
            "description": "Mock receipt extraction"
        })

    def extract_from_image(self, prompt: str, image_bytes: bytes, mime_type: str, **kwargs) -> str:
        return self.default_response


_active_vision_provider: Optional[VisionProvider] = None


def get_vision_provider() -> VisionProvider:
    """Returns the globally configured or default Vision provider."""
    global _active_vision_provider
    if _active_vision_provider is not None:
        return _active_vision_provider

    if settings.GEMINI_API_KEY:
        _active_vision_provider = GeminiVisionProvider()
    else:
        _active_vision_provider = MockVisionProvider()
    return _active_vision_provider


def set_vision_provider(provider: Optional[VisionProvider]):
    """Overrides the global Vision provider (useful for tests)."""
    global _active_vision_provider
    _active_vision_provider = provider

