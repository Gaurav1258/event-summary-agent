from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime, timezone

class EventLink(BaseModel):
    """Represents a single URL to an adverse media article or list."""
    url: HttpUrl
    source_name: Optional[str] = None

class CandidateHit(BaseModel):
    """The payload received from the screening engine."""
    candidate_id: str
    hit_id: str
    entity_name: str
    events: List[EventLink] = Field(default_factory=list)

class ScrapedArticle(BaseModel):
    """The result of scraping an EventLink."""
    url: HttpUrl
    title: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_success(self) -> bool:
        return self.content is not None and self.error is None
