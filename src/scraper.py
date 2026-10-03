import asyncio
import httpx
import trafilatura
import logging
from typing import List
from .schema import EventLink, ScrapedArticle

logger = logging.getLogger(__name__)

class ArticleScraper:
    """
    An asynchronous web scraper designed to fetch and extract clean text from 
    news articles and web pages concurrently.
    """
    def __init__(self, timeout: int = 15, max_concurrent: int = 10):
        self.timeout = timeout
        # Semaphore limits how many concurrent requests we make to avoid overwhelming the OS or triggering bot defenses
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def fetch_and_parse(self, client: httpx.AsyncClient, link: EventLink) -> ScrapedArticle:
        url_str = str(link.url)
        async with self.semaphore:
            try:
                # Mask as a standard browser to avoid basic bot protections
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                
                response = await client.get(url_str, headers=headers, follow_redirects=True)
                response.raise_for_status()
                
                # Trafilatura extracts only the main article text, ignoring navbars, footers, and ads.
                downloaded = response.text
                extracted_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
                
                if extracted_text:
                    return ScrapedArticle(url=link.url, content=extracted_text)
                else:
                    return ScrapedArticle(url=link.url, error="Trafilatura extracted no content.")
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} fetching {url_str}")
                return ScrapedArticle(url=link.url, error=f"HTTP Error: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"Network error fetching {url_str}: {str(e)}")
                return ScrapedArticle(url=link.url, error=f"Network Error: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error fetching {url_str}: {str(e)}")
                return ScrapedArticle(url=link.url, error=str(e))

    async def scrape_all(self, links: List[EventLink]) -> List[ScrapedArticle]:
        """Scrape a list of links concurrently."""
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=30)
        timeout = httpx.Timeout(self.timeout)
        
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            tasks = [self.fetch_and_parse(client, link) for link in links]
            
            # gather runs all tasks concurrently. return_exceptions=True prevents one crash from ruining the batch
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            cleaned_results = []
            for i, res in enumerate(results):
                if isinstance(res, Exception):
                    cleaned_results.append(ScrapedArticle(url=links[i].url, error=f"Fatal task error: {str(res)}"))
                else:
                    cleaned_results.append(res)
                    
            return cleaned_results
