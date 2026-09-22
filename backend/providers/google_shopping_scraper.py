"""
Google Shopping scraper using BeautifulSoup.
Scrapes product listings from Google Shopping which aggregates multiple retailers.
"""

from __future__ import annotations

import re
import urllib.parse
import random
from typing import Optional
import httpx
from bs4 import BeautifulSoup

from schemas import OfferOut, OfferProvider
from utils import parse_money
from .base import ProviderResult, _dedupe_offers


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
    }


def _safe_text(s: str) -> str:
    """Clean and normalize text."""
    return (s or "").replace("\n", " ").replace("\r", " ").strip()


def _extract_price(text: str) -> Optional[float]:
    """Extract price from text."""
    if not text:
        return None
    # Remove currency symbols and extract number
    text = text.replace("₹", "").replace("$", "").replace(",", "")
    m = re.search(r"([\d]+(?:\.\d{1,2})?)", text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except:
        return None


def _map_to_provider(seller: str) -> OfferProvider:
    """Map seller name to provider."""
    seller_lower = seller.lower()
    if "amazon" in seller_lower:
        return "amazon"
    elif "flipkart" in seller_lower:
        return "flipkart"
    elif "blinkit" in seller_lower or "grofers" in seller_lower:
        return "blinkit"
    elif "zepto" in seller_lower:
        return "zepto"
    elif "bigbasket" in seller_lower or "big basket" in seller_lower:
        return "bigbasket"
    else:
        # Default to amazon for unknown sellers
        return "amazon"


class GoogleShoppingScraper:
    """Scrapes Google Shopping for product listings."""
    
    async def search(
        self,
        *,
        query: str,
        max_results: int = 10,
        location: Optional[str] = None,
        timeout_s: float = 8.0,
    ) -> dict[OfferProvider, list[OfferOut]]:
        """Search Google Shopping and return results grouped by provider."""
        q = _safe_text(query)
        if not q:
            return {}
        
        # Google Shopping search URL
        search_url = f"https://www.google.com/search?tbm=shop&q={urllib.parse.quote(q)}"
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout_s),
                headers=get_headers(),
                follow_redirects=True,
            ) as client:
                resp = await client.get(search_url)
                if resp.status_code >= 400:
                    return {}
                html = resp.text
        except Exception:
            return {}
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Group offers by provider
        offers_by_provider: dict[OfferProvider, list[OfferOut]] = {
            "amazon": [],
            "flipkart": [],
            "blinkit": [],
            "zepto": [],
            "bigbasket": [],
        }
        
        # Find all product cards
        # Google Shopping uses various div structures
        products = soup.find_all('div', class_=re.compile(r'sh-dgr__content|sh-dlr__content'))
        
        if not products:
            # Try alternate structure
            products = soup.find_all('div', attrs={'data-docid': True})
        
        for product in products[:max_results * 2]:  # Get more to ensure we have enough per provider
            try:
                # Extract title
                title_elem = product.find('h3') or product.find('h4') or product.find('div', class_=re.compile(r'title'))
                if not title_elem:
                    continue
                title = _safe_text(title_elem.get_text())
                
                if not title:
                    continue
                
                # Extract price
                price_elem = product.find('span', class_=re.compile(r'price')) or product.find('b')
                price = None
                if price_elem:
                    price_text = price_elem.get_text()
                    price = _extract_price(price_text)
                
                # Extract seller/store
                seller_elem = product.find('div', class_=re.compile(r'merchant|seller|store'))
                seller = "Amazon"  # Default
                if seller_elem:
                    seller = _safe_text(seller_elem.get_text())
                
                # Map to provider
                provider = _map_to_provider(seller)
                
                # Extract image
                img_elem = product.find('img')
                image_url = None
                if img_elem:
                    image_url = img_elem.get('src') or img_elem.get('data-src')
                
                # Extract link
                link_elem = product.find('a', href=True)
                product_url = ""
                if link_elem:
                    href = link_elem['href']
                    # Google Shopping links are redirects, extract actual URL
                    if 'url=' in href:
                        try:
                            actual_url = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get('url', [''])[0]
                            product_url = actual_url
                        except:
                            product_url = href
                    else:
                        product_url = href
                
                if not product_url:
                    product_url = f"https://www.google.com/search?q={urllib.parse.quote(title)}"
                
                # Add to appropriate provider list
                if len(offers_by_provider[provider]) < max_results:
                    offers_by_provider[provider].append(OfferOut(
                        provider=provider,
                        title=title[:140],
                        price=price,
                        currency="INR",
                        url=product_url,
                        image_url=image_url,
                    ))
            except Exception:
                continue
        
        return offers_by_provider


async def get_google_shopping_results(query: str, max_results: int = 8) -> list:
    """Get results from Google Shopping and return as provider results."""
    scraper = GoogleShoppingScraper()
    offers_by_provider = await scraper.search(query=query, max_results=max_results)
    
    results = []
    for provider, offers in offers_by_provider.items():
        if offers:
            results.append(ProviderResult(
                provider=provider,
                offers=_dedupe_offers(offers),
                error=None
            ))
        else:
            results.append(ProviderResult(
                provider=provider,
                offers=[],
                error="no_results"
            ))
    
    return results


# Individual provider wrappers for compatibility
class GoogleShoppingAmazon:
    name: OfferProvider = "amazon"
    
    async def search(self, *, query: str, max_results: int, location: Optional[str] = None, timeout_s: float = 8.0) -> ProviderResult:
        scraper = GoogleShoppingScraper()
        offers_by_provider = await scraper.search(query=query, max_results=max_results, timeout_s=timeout_s)
        return ProviderResult(provider=self.name, offers=offers_by_provider.get(self.name, []), error=None)


class GoogleShoppingFlipkart:
    name: OfferProvider = "flipkart"
    
    async def search(self, *, query: str, max_results: int, location: Optional[str] = None, timeout_s: float = 8.0) -> ProviderResult:
        scraper = GoogleShoppingScraper()
        offers_by_provider = await scraper.search(query=query, max_results=max_results, timeout_s=timeout_s)
        return ProviderResult(provider=self.name, offers=offers_by_provider.get(self.name, []), error=None)


class GoogleShoppingBlinkit:
    name: OfferProvider = "blinkit"
    
    async def search(self, *, query: str, max_results: int, location: Optional[str] = None, timeout_s: float = 8.0) -> ProviderResult:
        scraper = GoogleShoppingScraper()
        offers_by_provider = await scraper.search(query=query, max_results=max_results, timeout_s=timeout_s)
        return ProviderResult(provider=self.name, offers=offers_by_provider.get(self.name, []), error=None)


class GoogleShoppingZepto:
    name: OfferProvider = "zepto"
    
    async def search(self, *, query: str, max_results: int, location: Optional[str] = None, timeout_s: float = 8.0) -> ProviderResult:
        scraper = GoogleShoppingScraper()
        offers_by_provider = await scraper.search(query=query, max_results=max_results, timeout_s=timeout_s)
        return ProviderResult(provider=self.name, offers=offers_by_provider.get(self.name, []), error=None)


class GoogleShoppingBigBasket:
    name: OfferProvider = "bigbasket"
    
    async def search(self, *, query: str, max_results: int, location: Optional[str] = None, timeout_s: float = 8.0) -> ProviderResult:
        scraper = GoogleShoppingScraper()
        offers_by_provider = await scraper.search(query=query, max_results=max_results, timeout_s=timeout_s)
        return ProviderResult(provider=self.name, offers=offers_by_provider.get(self.name, []), error=None)


def get_google_shopping_scrapers() -> list:
    """Return Google Shopping scrapers for all providers."""
    return [
        GoogleShoppingAmazon(),
        GoogleShoppingFlipkart(),
        GoogleShoppingBlinkit(),
        GoogleShoppingZepto(),
        GoogleShoppingBigBasket(),
    ]
