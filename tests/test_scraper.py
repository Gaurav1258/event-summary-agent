import asyncio
import os
import sys

# Ensure Python can find our 'src' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.schema import EventLink
from src.scraper import ArticleScraper

async def test_scraper():
    # Let's test with a real news article and a fake one to see error handling
    links = [
        EventLink(url="https://en.wikipedia.org/wiki/Money_laundering"),
        EventLink(url="https://www.bbc.com/news/business-68194488"),
        EventLink(url="https://example.com/this-page-definitely-does-not-exist-1234")
    ]
    
    print(f"Scraping {len(links)} links asynchronously...")
    scraper = ArticleScraper(timeout=10, max_concurrent=5)
    
    results = await scraper.scrape_all(links)
    
    for res in results:
        print(f"\n[{'SUCCESS' if res.is_success else 'FAILED'}] URL: {res.url}")
        if res.is_success:
            print(f"-> Extracted {len(res.content)} characters.")
            print(f"-> Snippet: {res.content[:150]}...")
        else:
            print(f"-> Error Reason: {res.error}")

if __name__ == "__main__":
    asyncio.run(test_scraper())
