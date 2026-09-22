"""
Enhanced scrapers with better headers to bypass anti-bot protection.
Uses realistic browser headers and user agents.
"""

from __future__ import annotations

import re
import urllib.parse
import random
from typing import Optional
import httpx

from schemas import OfferOut, OfferProvider
from utils import parse_money
from .base import ProviderResult, _dedupe_offers


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def get_headers() -> dict:
    """Get realistic browser headers."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }


def _safe_text(s: str) -> str:
    """Clean and normalize text."""
    return (s or "").replace("\n", " ").replace("\r", " ").strip()


def _extract_price(text: str) -> Optional[float]:
    """Extract price from text."""
    if not text:
        return None
    m = re.search(r"₹?\s?([\d,]+(?:\.\d{1,2})?)", text)
    if not m:
        return None
    return parse_money(m.group(1))


# For now, use mock data with realistic prices
# Real scraping requires either:
# 1. Playwright/Selenium (needs C++ build tools on Windows)
# 2. Paid proxy service (ScraperAPI, Bright Data)
# 3. Official APIs (not available for most sites)

class EnhancedMockScraper:
    """Enhanced mock scraper with realistic data."""
    
    def __init__(self, provider: OfferProvider):
        self.name = provider
        self._base_prices = {
            "rice": 450,
            "dal": 180,
            "oil": 220,
            "sugar": 45,
            "atta": 380,
            "milk": 60,
            "bread": 40,
            "eggs": 80,
            "chicken": 280,
            "fish": 350,
            "vegetables": 50,
            "fruits": 120,
            "coffee": 350,
            "tea": 180,
            "biscuits": 50,
            "noodles": 35,
            "sauce": 90,
            "spices": 120,
            "soap": 45,
            "shampoo": 180,
        }
    
    def _get_base_price(self, query: str) -> float:
        """Get base price for query."""
        q_lower = query.lower()
        for keyword, price in self._base_prices.items():
            if keyword in q_lower:
                return price
        return 250  # Default
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 6.0,
    ) -> ProviderResult:
        """Generate realistic mock product data with real URLs."""
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        base_price = self._get_base_price(q)
        
        # Provider-specific pricing
        price_multipliers = {
            "amazon": 0.95,      # Usually cheapest
            "flipkart": 1.02,    # Slightly higher
            "blinkit": 1.15,     # Quick commerce premium
            "zepto": 1.12,       # Quick commerce premium
            "bigbasket": 1.05,   # Moderate
        }
        
        multiplier = price_multipliers.get(self.name, 1.0)
        
        # Real base URLs for each provider
        base_urls = {
            "amazon": "https://www.amazon.in/s?k=",
            "flipkart": "https://www.flipkart.com/search?q=",
            "blinkit": "https://blinkit.com/s/?q=",
            "zepto": "https://www.zeptonow.com/search?query=",
            "bigbasket": "https://www.bigbasket.com/ps/?q=",
        }
        
        offers = []
        product_variants = [
            f"{q.title()}",
            f"{q.title()} - Premium",
            f"{q.title()} - Organic",
            f"{q.title()} - Value Pack",
            f"{q.title()} - Fresh",
        ]
        
        for i in range(min(max_results, 5)):
            variance = random.uniform(0.92, 1.08)
            price = round(base_price * multiplier * variance, 2)
            
            # Use real search URLs
            search_query = urllib.parse.quote(product_variants[i])
            product_url = base_urls.get(self.name, "") + search_query
            
            # Use a working placeholder service or real product image
            image_url = f"https://placehold.co/200x200/4A90E2/FFFFFF/png?text={self.name.title()}"
            
            offers.append(OfferOut(
                provider=self.name,
                title=product_variants[i][:140],
                price=price,
                currency="INR",
                url=product_url,
                image_url=image_url,
            ))
        
        return ProviderResult(provider=self.name, offers=offers, error=None)


def get_enhanced_scrapers() -> list:
    """Return enhanced scrapers."""
    return [
        EnhancedMockScraper("amazon"),
        EnhancedMockScraper("flipkart"),
        EnhancedMockScraper("blinkit"),
        EnhancedMockScraper("zepto"),
        EnhancedMockScraper("bigbasket"),
    ]
