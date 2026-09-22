#!/usr/bin/env python3
"""Quick test of site scrapers"""

import asyncio
from providers.site_scrapers import get_site_scrapers

async def test():
    scrapers = get_site_scrapers()
    print(f"Testing {len(scrapers)} scrapers...\n")
    
    for scraper in scrapers:
        print(f"Testing {scraper.name.upper()}...")
        try:
            result = await scraper.search(query="rice", max_results=3, timeout_s=5.0)
            print(f"  ✓ Found {len(result.offers)} offers")
            if result.error:
                print(f"  ⚠ Error: {result.error}")
            for i, offer in enumerate(result.offers[:2]):
                print(f"    [{i+1}] {offer.title[:40]}")
                print(f"        Price: {offer.price} {offer.currency}")
                print(f"        Image: {'✓' if offer.image_url else '✗'}")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        print()

if __name__ == "__main__":
    asyncio.run(test())
