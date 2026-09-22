"""
Web search adapter - now uses site-specific scrapers.
Kept for backward compatibility and fallback.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Optional

import httpx

from schemas import OfferOut, OfferProvider
from utils import parse_money
from .base import ProviderResult, _dedupe_offers
from .site_scrapers import get_site_scrapers


_PRICE_RE = re.compile(r"(₹|\$|€|£)\s?[\d,]+(?:\.\d{1,2})?")


def _currency_from_text(t: str) -> str:
    if "₹" in t:
        return "INR"
    if "$" in t:
        return "USD"
    if "€" in t:
        return "EUR"
    if "£" in t:
        return "GBP"
    return "INR"


def _extract_price(text: str) -> Optional[float]:
    if not text:
        return None
    m = _PRICE_RE.search(text)
    if not m:
        return None
    return parse_money(m.group(0))


def _safe_text(s: str) -> str:
    return (s or "").replace("\n", " ").replace("\r", " ").strip()


def _safe_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return u
    if not (u.startswith("http://") or u.startswith("https://")):
        return ""
    return u


async def _fetch_image_url(url: str, *, timeout_s: float = 3.0) -> Optional[str]:
    """
    Best-effort item image fetch via OpenGraph/Twitter meta tags.
    """
    url = _safe_url(url)
    if not url:
        return None
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_s),
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                return None
            html = resp.text or ""
    except Exception:
        return None

    m = re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE) or \
        re.search(r'name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if not m:
        return None
    img = m.group(1).strip()
    if not img:
        return None
    if img.startswith("//"):
        img = "https:" + img
    if img.startswith("/"):
        try:
            parsed = urllib.parse.urlparse(url)
            img = f"{parsed.scheme}://{parsed.netloc}{img}"
        except Exception:
            return None
    return _safe_url(img) or None


def default_offer_providers() -> list:
    """Return all available offer providers."""
    # Use Google Shopping scraper with BeautifulSoup
    try:
        from .google_shopping_scraper import get_google_shopping_scrapers
        return get_google_shopping_scrapers()
    except ImportError:
        # Fallback to enhanced mock if BeautifulSoup not installed
        from .enhanced_scrapers import get_enhanced_scrapers
        return get_enhanced_scrapers()
