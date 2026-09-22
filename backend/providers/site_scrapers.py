"""
Direct scrapers for Indian e-commerce platforms.
Scrapes product names, images, prices directly from sites.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Optional
import httpx

from schemas import OfferOut, OfferProvider
from utils import parse_money
from .base import ProviderResult, _dedupe_offers


def _safe_text(s: str) -> str:
    """Clean and normalize text."""
    return (s or "").replace("\n", " ").replace("\r", " ").strip()


def _safe_url(u: str) -> str:
    """Validate and clean URLs."""
    u = (u or "").strip()
    if not u:
        return u
    if not (u.startswith("http://") or u.startswith("https://")):
        return ""
    return u


def _extract_price(text: str) -> Optional[float]:
    """Extract price from text."""
    if not text:
        return None
    # Match ₹1,234.50 or ₹1234 or 1,234.50
    m = re.search(r"₹?\s?([\d,]+(?:\.\d{1,2})?)", text)
    if not m:
        return None
    return parse_money(m.group(1))


# ============================================================================
# AMAZON INDIA SCRAPER
# ============================================================================

class AmazonIndiaScraper:
    name: OfferProvider = "amazon"
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 6.0,
    ) -> ProviderResult:
        """Search Amazon India directly."""
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        search_url = f"https://www.amazon.in/s?k={urllib.parse.quote(q)}"
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout_s),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get(search_url)
                if resp.status_code >= 400:
                    return ProviderResult(provider=self.name, offers=[], error="fetch_failed")
                html = resp.text or ""
        except Exception as e:
            return ProviderResult(provider=self.name, offers=[], error=f"fetch_error:{type(e).__name__}")
        
        offers: list[OfferOut] = []
        
        # Find all product divs with data-asin
        for match in re.finditer(r'data-asin="([^"]+)"[^>]*data-index', html):
            asin = match.group(1)
            if not asin or asin == "":
                continue
            
            # Get the product block
            start = match.start()
            end = start + 3000
            block = html[start:end]
            
            # Extract title
            title_match = re.search(r'<span[^>]*class="[^"]*a-text-normal[^"]*"[^>]*>([^<]+)</span>', block)
            if not title_match:
                title_match = re.search(r'<h2[^>]*>.*?<span[^>]*>([^<]+)</span>', block, re.DOTALL)
            
            if not title_match:
                continue
            
            title = _safe_text(title_match.group(1))
            
            # Extract price
            price_match = re.search(r'<span[^>]*class="[^"]*a-price-whole[^"]*"[^>]*>([^<]+)</span>', block)
            price = None
            if price_match:
                price = _extract_price(price_match.group(1))
            
            # Extract image
            img_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*class="[^"]*s-image[^"]*"', block)
            image_url = None
            if img_match:
                image_url = _safe_url(img_match.group(1))
            
            # Build product URL
            product_url = f"https://www.amazon.in/dp/{asin}"
            
            offers.append(OfferOut(
                provider=self.name,
                title=title[:140],
                price=price,
                currency="INR",
                url=product_url,
                image_url=image_url,
            ))
            
            if len(offers) >= max_results:
                break
        
        return ProviderResult(provider=self.name, offers=_dedupe_offers(offers), error=None)


# ============================================================================
# FLIPKART SCRAPER
# ============================================================================

class FlipkartScraper:
    name: OfferProvider = "flipkart"
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 6.0,
    ) -> ProviderResult:
        """Search Flipkart directly."""
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        search_url = f"https://www.flipkart.com/search?q={urllib.parse.quote(q)}"
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout_s),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get(search_url)
                if resp.status_code >= 400:
                    return ProviderResult(provider=self.name, offers=[], error="fetch_failed")
                html = resp.text or ""
        except Exception as e:
            return ProviderResult(provider=self.name, offers=[], error=f"fetch_error:{type(e).__name__}")
        
        offers: list[OfferOut] = []
        
        # Find product links
        for match in re.finditer(r'<a[^>]*href="(/[^"]*?/p/[^"]+)"[^>]*>', html):
            product_path = match.group(1)
            
            # Get the product block
            start = match.start()
            end = start + 2000
            block = html[start:end]
            
            # Extract title
            title_match = re.search(r'<div[^>]*class="[^"]*KzDlHZ[^"]*"[^>]*>([^<]+)</div>', block)
            if not title_match:
                title_match = re.search(r'<a[^>]*class="[^"]*wjcEIp[^"]*"[^>]*>([^<]+)</a>', block)
            if not title_match:
                title_match = re.search(r'alt="([^"]+)"', block)
            
            if not title_match:
                continue
            
            title = _safe_text(title_match.group(1))
            
            # Extract price
            price_match = re.search(r'₹([\d,]+)', block)
            price = None
            if price_match:
                price = _extract_price(price_match.group(1))
            
            # Extract image
            img_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*>', block)
            image_url = None
            if img_match:
                img_url = img_match.group(1)
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                image_url = _safe_url(img_url)
            
            # Build product URL
            product_url = f"https://www.flipkart.com{product_path}"
            
            offers.append(OfferOut(
                provider=self.name,
                title=title[:140],
                price=price,
                currency="INR",
                url=product_url,
                image_url=image_url,
            ))
            
            if len(offers) >= max_results:
                break
        
        return ProviderResult(provider=self.name, offers=_dedupe_offers(offers), error=None)


# ============================================================================
# BLINKIT SCRAPER
# ============================================================================

class BlinkitScraper:
    name: OfferProvider = "blinkit"
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 6.0,
    ) -> ProviderResult:
        """Search Blinkit directly."""
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        search_url = f"https://blinkit.com/s/?q={urllib.parse.quote(q)}"
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout_s),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get(search_url)
                if resp.status_code >= 400:
                    return ProviderResult(provider=self.name, offers=[], error="fetch_failed")
                html = resp.text or ""
        except Exception as e:
            return ProviderResult(provider=self.name, offers=[], error=f"fetch_error:{type(e).__name__}")
        
        offers: list[OfferOut] = []
        
        # Find product data in JSON
        json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>([^<]+)</script>', html)
        if json_match:
            try:
                import json
                data = json.loads(json_match.group(1))
                products = []
                
                # Navigate JSON structure to find products
                if "props" in data and "pageProps" in data["props"]:
                    page_props = data["props"]["pageProps"]
                    if "products" in page_props:
                        products = page_props["products"]
                
                for product in products[:max_results]:
                    title = product.get("name", "")
                    price = product.get("price")
                    image_url = product.get("image_url")
                    product_id = product.get("id", "")
                    
                    if not title:
                        continue
                    
                    product_url = f"https://blinkit.com/prn/{product_id}"
                    
                    offers.append(OfferOut(
                        provider=self.name,
                        title=title[:140],
                        price=price,
                        currency="INR",
                        url=product_url,
                        image_url=image_url,
                    ))
            except Exception:
                pass
        
        return ProviderResult(provider=self.name, offers=_dedupe_offers(offers), error=None)


# ============================================================================
# ZEPTO SCRAPER
# ============================================================================

class ZeptoScraper:
    name: OfferProvider = "zepto"
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 6.0,
    ) -> ProviderResult:
        """Search Zepto directly."""
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        search_url = f"https://www.zeptonow.com/search?query={urllib.parse.quote(q)}"
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout_s),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get(search_url)
                if resp.status_code >= 400:
                    return ProviderResult(provider=self.name, offers=[], error="fetch_failed")
                html = resp.text or ""
        except Exception as e:
            return ProviderResult(provider=self.name, offers=[], error=f"fetch_error:{type(e).__name__}")
        
        offers: list[OfferOut] = []
        
        # Find product data in JSON
        json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>([^<]+)</script>', html)
        if json_match:
            try:
                import json
                data = json.loads(json_match.group(1))
                products = []
                
                # Navigate JSON structure
                if "props" in data and "pageProps" in data["props"]:
                    page_props = data["props"]["pageProps"]
                    if "products" in page_props:
                        products = page_props["products"]
                    elif "initialState" in page_props:
                        # Try alternate structure
                        state = page_props["initialState"]
                        if "products" in state:
                            products = state["products"]
                
                for product in products[:max_results]:
                    title = product.get("name", "")
                    price = product.get("price", product.get("selling_price"))
                    image_url = product.get("image", product.get("image_url"))
                    product_id = product.get("id", "")
                    
                    if not title:
                        continue
                    
                    product_url = f"https://www.zeptonow.com/pn/{product_id}"
                    
                    offers.append(OfferOut(
                        provider=self.name,
                        title=title[:140],
                        price=price,
                        currency="INR",
                        url=product_url,
                        image_url=image_url,
                    ))
            except Exception:
                pass
        
        return ProviderResult(provider=self.name, offers=_dedupe_offers(offers), error=None)


# ============================================================================
# BIGBASKET SCRAPER
# ============================================================================

class BigBasketScraper:
    name: OfferProvider = "bigbasket"
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 6.0,
    ) -> ProviderResult:
        """Search BigBasket directly."""
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        search_url = f"https://www.bigbasket.com/ps/?q={urllib.parse.quote(q)}"
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout_s),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get(search_url)
                if resp.status_code >= 400:
                    return ProviderResult(provider=self.name, offers=[], error="fetch_failed")
                html = resp.text or ""
        except Exception as e:
            return ProviderResult(provider=self.name, offers=[], error=f"fetch_error:{type(e).__name__}")
        
        offers: list[OfferOut] = []
        
        # Find product links
        for match in re.finditer(r'<a[^>]*href="(/pd/[^"]+)"[^>]*>', html):
            product_path = match.group(1)
            
            # Get the product block
            start = match.start()
            end = start + 2000
            block = html[start:end]
            
            # Extract title
            title_match = re.search(r'<h3[^>]*>([^<]+)</h3>', block)
            if not title_match:
                title_match = re.search(r'alt="([^"]+)"', block)
            
            if not title_match:
                continue
            
            title = _safe_text(title_match.group(1))
            
            # Extract price
            price_match = re.search(r'₹\s*([\d,]+(?:\.\d{2})?)', block)
            price = None
            if price_match:
                price = _extract_price(price_match.group(1))
            
            # Extract image
            img_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*>', block)
            image_url = None
            if img_match:
                img_url = img_match.group(1)
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                image_url = _safe_url(img_url)
            
            # Build product URL
            product_url = f"https://www.bigbasket.com{product_path}"
            
            offers.append(OfferOut(
                provider=self.name,
                title=title[:140],
                price=price,
                currency="INR",
                url=product_url,
                image_url=image_url,
            ))
            
            if len(offers) >= max_results:
                break
        
        return ProviderResult(provider=self.name, offers=_dedupe_offers(offers), error=None)


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_site_scrapers() -> list:
    """Return all site-specific scrapers."""
    # Note: Most sites block direct scraping. Using mock data for demo.
    # In production, use official APIs or headless browser (Playwright/Selenium)
    return [
        AmazonIndiaScraper(),
        FlipkartScraper(),
        BlinkitScraper(),
        ZeptoScraper(),
        BigBasketScraper(),
    ]


# ============================================================================
# MOCK DATA GENERATOR (for demo when sites block scraping)
# ============================================================================

class MockDataGenerator:
    """Generates realistic mock data when sites block scraping."""
    
    def __init__(self, provider: OfferProvider):
        self.name = provider
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 6.0,
    ) -> ProviderResult:
        """Generate mock product data."""
        import random
        
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        # Generate realistic prices based on provider
        base_price = random.randint(200, 800)
        price_variance = {
            "amazon": 0.95,      # Usually cheapest
            "flipkart": 1.02,    # Slightly higher
            "blinkit": 1.15,     # Quick commerce premium
            "zepto": 1.12,       # Quick commerce premium
            "bigbasket": 1.05,   # Moderate
        }
        
        offers = []
        for i in range(min(max_results, 5)):
            variance = price_variance.get(self.name, 1.0)
            price = round(base_price * variance * random.uniform(0.95, 1.05), 2)
            
            offers.append(OfferOut(
                provider=self.name,
                title=f"{q.title()} - {self.name.title()} Product {i+1}",
                price=price,
                currency="INR",
                url=f"https://www.{self.name}.com/product/{i+1}",
                image_url=f"https://via.placeholder.com/150?text={self.name}+{i+1}",
            ))
        
        return ProviderResult(provider=self.name, offers=offers, error=None)


def get_mock_scrapers() -> list:
    """Return mock scrapers for demo (when sites block real scraping)."""
    return [
        MockDataGenerator("amazon"),
        MockDataGenerator("flipkart"),
        MockDataGenerator("blinkit"),
        MockDataGenerator("zepto"),
        MockDataGenerator("bigbasket"),
    ]
