"""
Playwright-based scrapers for e-commerce sites.
Uses headless browser to bypass anti-bot protection.
"""

from __future__ import annotations

import re
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page

from schemas import OfferOut, OfferProvider
from utils import parse_money
from .base import ProviderResult, _dedupe_offers


# Global browser instance (reused across requests)
_browser: Optional[Browser] = None
_browser_lock = asyncio.Lock()


async def get_browser() -> Browser:
    """Get or create browser instance."""
    global _browser
    async with _browser_lock:
        if _browser is None or not _browser.is_connected():
            playwright = await async_playwright().start()
            _browser = await playwright.chromium.launch(headless=True)
        return _browser


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


# ============================================================================
# AMAZON INDIA SCRAPER
# ============================================================================

class AmazonPlaywrightScraper:
    name: OfferProvider = "amazon"
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 10.0,
    ) -> ProviderResult:
        """Search Amazon India using Playwright."""
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        try:
            browser = await get_browser()
            page = await browser.new_page()
            
            # Navigate to search
            import urllib.parse
            search_url = f"https://www.amazon.in/s?k={urllib.parse.quote(q)}"
            await page.goto(search_url, timeout=timeout_s * 1000)
            
            # Wait for results
            await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=5000)
            
            offers = []
            
            # Get all product cards
            products = await page.query_selector_all('[data-component-type="s-search-result"]')
            
            for product in products[:max_results]:
                try:
                    # Extract ASIN
                    asin = await product.get_attribute('data-asin')
                    if not asin:
                        continue
                    
                    # Extract title
                    title_elem = await product.query_selector('h2 a span')
                    title = await title_elem.inner_text() if title_elem else ""
                    title = _safe_text(title)
                    
                    if not title:
                        continue
                    
                    # Extract price
                    price_elem = await product.query_selector('.a-price-whole')
                    price = None
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        price = _extract_price(price_text)
                    
                    # Extract image
                    img_elem = await product.query_selector('img.s-image')
                    image_url = None
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
                    # Build URL
                    product_url = f"https://www.amazon.in/dp/{asin}"
                    
                    offers.append(OfferOut(
                        provider=self.name,
                        title=title[:140],
                        price=price,
                        currency="INR",
                        url=product_url,
                        image_url=image_url,
                    ))
                except Exception:
                    continue
            
            await page.close()
            return ProviderResult(provider=self.name, offers=_dedupe_offers(offers), error=None)
            
        except Exception as e:
            return ProviderResult(provider=self.name, offers=[], error=f"playwright_error:{type(e).__name__}")


# ============================================================================
# FLIPKART SCRAPER
# ============================================================================

class FlipkartPlaywrightScraper:
    name: OfferProvider = "flipkart"
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 10.0,
    ) -> ProviderResult:
        """Search Flipkart using Playwright."""
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        try:
            browser = await get_browser()
            page = await browser.new_page()
            
            import urllib.parse
            search_url = f"https://www.flipkart.com/search?q={urllib.parse.quote(q)}"
            await page.goto(search_url, timeout=timeout_s * 1000)
            
            # Wait for results
            await page.wait_for_selector('[data-id]', timeout=5000)
            
            offers = []
            
            # Get all product cards
            products = await page.query_selector_all('[data-id]')
            
            for product in products[:max_results]:
                try:
                    # Extract title
                    title_elem = await product.query_selector('a[title], div.KzDlHZ, a.wjcEIp')
                    if not title_elem:
                        continue
                    
                    title = await title_elem.get_attribute('title')
                    if not title:
                        title = await title_elem.inner_text()
                    title = _safe_text(title)
                    
                    if not title:
                        continue
                    
                    # Extract price
                    price_elem = await product.query_selector('div.Nx9bqj, div._4b5DiR')
                    price = None
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        price = _extract_price(price_text)
                    
                    # Extract image
                    img_elem = await product.query_selector('img')
                    image_url = None
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                        if image_url and image_url.startswith('//'):
                            image_url = 'https:' + image_url
                    
                    # Extract URL
                    link_elem = await product.query_selector('a[href*="/p/"]')
                    product_url = ""
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://www.flipkart.com{href}" if href.startswith('/') else href
                    
                    if not product_url:
                        continue
                    
                    offers.append(OfferOut(
                        provider=self.name,
                        title=title[:140],
                        price=price,
                        currency="INR",
                        url=product_url,
                        image_url=image_url,
                    ))
                except Exception:
                    continue
            
            await page.close()
            return ProviderResult(provider=self.name, offers=_dedupe_offers(offers), error=None)
            
        except Exception as e:
            return ProviderResult(provider=self.name, offers=[], error=f"playwright_error:{type(e).__name__}")


# ============================================================================
# BLINKIT SCRAPER
# ============================================================================

class BlinkitPlaywrightScraper:
    name: OfferProvider = "blinkit"
    
    async def search(
        self,
        *,
        query: str,
        max_results: int,
        location: Optional[str] = None,
        timeout_s: float = 10.0,
    ) -> ProviderResult:
        """Search Blinkit using Playwright."""
        q = _safe_text(query)
        if not q:
            return ProviderResult(provider=self.name, offers=[], error="empty_query")
        
        try:
            browser = await get_browser()
            page = await browser.new_page()
            
            import urllib.parse
            search_url = f"https://blinkit.com/s/?q={urllib.parse.quote(q)}"
            await page.goto(search_url, timeout=timeout_s * 1000)
            
            # Wait for results
            await page.wait_for_selector('[class*="Product"]', timeout=5000)
            
            offers = []
            
            # Get all product cards
            products = await page.query_selector_all('[class*="Product"]')
            
            for product in products[:max_results]:
                try:
                    # Extract title
                    title_elem = await product.query_selector('[class*="ProductName"], [class*="product-name"]')
                    if not title_elem:
                        continue
                    
                    title = await title_elem.inner_text()
                    title = _safe_text(title)
                    
                    if not title:
                        continue
                    
                    # Extract price
                    price_elem = await product.query_selector('[class*="Price"], [class*="price"]')
                    price = None
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        price = _extract_price(price_text)
                    
                    # Extract image
                    img_elem = await product.query_selector('img')
                    image_url = None
                    if img_elem:
                        image_url = await img_elem.get_attribute('src')
                    
                    # Extract URL
                    link_elem = await product.query_selector('a')
                    product_url = ""
                    if link_elem:
                        href = await link_elem.get_attribute('href')
                        if href:
                            product_url = f"https://blinkit.com{href}" if href.startswith('/') else href
                    
                    if not product_url:
                        product_url = f"https://blinkit.com/search?q={urllib.parse.quote(title)}"
                    
                    offers.append(OfferOut(
                        provider=self.name,
                        title=title[:140],
                        price=price,
                        currency="INR",
                        url=product_url,
                        image_url=image_url,
                    ))
                except Exception:
                    continue
            
            await page.close()
            return ProviderResult(provider=self.name, offers=_dedupe_offers(offers), error=None)
            
        except Exception as e:
            return ProviderResult(provider=self.name, offers=[], error=f"playwright_error:{type(e).__name__}")


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_playwright_scrapers() -> list:
    """Return all Playwright-based scrapers."""
    return [
        AmazonPlaywrightScraper(),
        FlipkartPlaywrightScraper(),
        BlinkitPlaywrightScraper(),
    ]
