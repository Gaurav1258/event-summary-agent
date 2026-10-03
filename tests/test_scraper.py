import asyncio
import os
import sys

# Ensure Python can find our 'src' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.schema import EventLink
from src.scraper import ArticleScraper

@pytest.mark.asyncio
async def test_scraper():
    # Let's test with a real news article and a fake one to see error handling
    links = [
        EventLink(url="https://en.wikipedia.org/wiki/Money_laundering"),
        EventLink(url="https://example.com/this-page-definitely-does-not-exist-1234")
    ]
    
    print(f"Scraping {len(links)} links asynchronously...")
    scraper = ArticleScraper(timeout=10, max_concurrent=5)
    
    results = await scraper.scrape_all(links)
    assert len(results) == 2
    assert results[0].is_success is True
    assert len(results[0].content) > 500
    assert results[1].is_success is False
    assert results[1].error is not None

if __name__ == "__main__":
    asyncio.run(test_scraper())
