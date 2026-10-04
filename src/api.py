import os
import json
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .schema import CandidateHit, SummaryResponse, ScrapingStats
from .scraper import ArticleScraper
from .llm import SummarizationEngine

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("event-summary-api")

# Global dependencies with lazy initialization
_scraper: ArticleScraper = None
_llm_engine: SummarizationEngine = None

def get_scraper() -> ArticleScraper:
    global _scraper
    if _scraper is None:
        _scraper = ArticleScraper(timeout=15, max_concurrent=10)
    return _scraper

def get_llm_engine() -> SummarizationEngine:
    global _llm_engine
    if _llm_engine is None:
        project_id = os.environ.get("GCP_PROJECT_ID", "mlops2215")
        region = os.environ.get("GCP_REGION", "us-central1")
        _llm_engine = SummarizationEngine(project_id=project_id, location=region)
    return _llm_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Event Summary Agent.")
    get_scraper()
    get_llm_engine()
    yield
    logger.info("Shutting down Event Summary Agent.")

app = FastAPI(
    title="Namelist Screening Event Summary Agent",
    description="Automated adverse media extraction and Map-Reduce summarization agent for screening engine hits.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for UI integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Health check endpoint for Cloud Run and container orchestrators."""
    return {
        "status": "healthy",
        "service": "event-summary-agent",
        "project_id": os.environ.get("GCP_PROJECT_ID", "mlops2215"),
        "version": "1.0.0"
    }

@app.get("/api/v1/candidates", tags=["Screening"])
async def get_candidate_hits():
    """Returns pre-loaded candidate screening hits with adverse media links for the UI."""
    data_path = os.path.join(os.path.dirname(__file__), "data", "candidate_hits.json")
    if not os.path.exists(data_path):
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "candidate_hits.json")
        
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.post("/api/v1/summarize", response_model=SummaryResponse, tags=["Screening"])
async def summarize_candidate_hit(payload: CandidateHit):
    """
    Main endpoint: Accepts a candidate profile and up to 100 event links.
    Scrapes the articles concurrently, extracts adverse media facts (Map step),
    and synthesizes a final Investigator Report (Reduce step).
    """
    logger.info(f"Received screening request for {payload.entity_name} (Hit: {payload.hit_id}) with {len(payload.events)} event links.")
    
    if not payload.events:
        return SummaryResponse(
            candidate_id=payload.candidate_id,
            hit_id=payload.hit_id,
            entity_name=payload.entity_name,
            stats=ScrapingStats(total_links=0, successful_scrapes=0, failed_scrapes=0),
            summary_report="### Screening Summary\n\nNo event links were provided for this hit."
        )

    try:
        # Step 1: Scrape all links concurrently
        logger.info(f"Scraping {len(payload.events)} URLs concurrently...")
        current_scraper = get_scraper()
        current_llm = get_llm_engine()
        scraped_articles = await current_scraper.scrape_all(payload.events)
        
        successful = sum(1 for a in scraped_articles if a.is_success)
        failed = len(scraped_articles) - successful
        logger.info(f"Scraping completed: {successful} succeeded, {failed} failed.")
        
        # Step 2: Map-Reduce Summarization via Vertex AI
        logger.info("Running Map-Reduce LLM summarization pipeline...")
        report = await current_llm.generate_report(candidate=payload, articles=scraped_articles)
        
        return SummaryResponse(
            candidate_id=payload.candidate_id,
            hit_id=payload.hit_id,
            entity_name=payload.entity_name,
            stats=ScrapingStats(
                total_links=len(payload.events),
                successful_scrapes=successful,
                failed_scrapes=failed
            ),
            summary_report=report
        )
        
    except Exception as e:
        logger.error(f"Error processing screening hit {payload.hit_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the summary: {str(e)}"
        )
