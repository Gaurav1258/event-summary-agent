import os
import sys
import pytest
from httpx import ASGITransport, AsyncClient

# Ensure Python can find our 'src' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api import app

@pytest.mark.asyncio
async def test_health_check():
    """Verify that the health check endpoint returns 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "event-summary-agent"

@pytest.mark.asyncio
async def test_empty_events_payload():
    """Verify that the API gracefully handles an empty events array."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "candidate_id": "CAND-001",
            "hit_id": "HIT-9999",
            "entity_name": "Test Entity",
            "events": []
        }
        response = await client.post("/api/v1/summarize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_links"] == 0
        assert "No event links were provided" in data["summary_report"]

@pytest.mark.asyncio
async def test_end_to_end_summarize():
    """
    Full End-to-End integration test:
    FastAPI receives payload -> Scrapes real URL -> Map (Gemini 2.5 Flash) -> Reduce (Gemini 2.5 Pro) -> Formats Summary.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "candidate_id": "CAND-MADOFF-001",
            "hit_id": "HIT-78901",
            "entity_name": "Bernard Madoff",
            "events": [
                {"url": "https://en.wikipedia.org/wiki/Bernard_Madoff", "source_name": "Wikipedia"},
                {"url": "https://example.com/dead-link-404-test", "source_name": "Broken Source"}
            ]
        }
        
        response = await client.post("/api/v1/summarize", json=payload, timeout=60.0)
        assert response.status_code == 200
        data = response.json()
        
        assert data["candidate_id"] == "CAND-MADOFF-001"
        assert data["entity_name"] == "Bernard Madoff"
        assert data["stats"]["total_links"] == 2
        assert data["stats"]["successful_scrapes"] == 1
        assert data["stats"]["failed_scrapes"] == 1
        assert len(data["summary_report"]) > 100
        assert "Ponzi" in data["summary_report"] or "fraud" in data["summary_report"].lower()
