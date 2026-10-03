import asyncio
import logging
from typing import List, Optional
from google import genai
from google.genai import types

from .schema import CandidateHit, ScrapedArticle

logger = logging.getLogger(__name__)

class SummarizationEngine:
    """
    Orchestrates the Map-Reduce LLM flow using Google Vertex AI.
    """
    def __init__(self, project_id: str, location: str = "us-central1"):
        # We explicitly enable Vertex AI mode for enterprise-grade GCP integration
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        
        # MAP: We use Gemini 2.5 Flash for fast, cost-effective parallel extraction
        self.map_model = "gemini-2.5-flash"
        
        # REDUCE: We use Gemini 2.5 Pro for nuanced synthesis and report writing
        self.reduce_model = "gemini-2.5-pro"

    async def _map_article(self, article: ScrapedArticle, candidate_name: str) -> Optional[str]:
        """
        Map Step: Analyzes a single article to extract facts about the candidate.
        Runs in parallel for all 100 articles.
        """
        if not article.is_success:
            return None
            
        prompt = f"""
        You are an expert financial crimes investigator.
        Read the following article and extract any adverse media or risk-relevant facts specifically regarding the entity/person named: '{candidate_name}'.
        
        CRITICAL RULES:
        - If the article does NOT mention this exact entity, reply strictly with "NO_MATCH".
        - If the article mentions them but there are NO adverse media or risk-relevant findings (e.g. positive news, sports, unrelated business), reply strictly with "NO_MATCH".
        - Do not output explanations like "no adverse media found". Reply ONLY with "NO_MATCH".
        - If and only if there ARE adverse findings or risks, provide a concise, bulleted list of the adverse facts.
        
        Article URL: {article.url}
        Article Content:
        {article.content[:25000]}
        """
        
        try:
            # We use asyncio.to_thread so the synchronous SDK calls don't block the async event loop
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.map_model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1) # Low temp for factual extraction
            )
            result = response.text.strip()
            
            if "NO_MATCH" in result:
                return None
                
            return f"From {article.url}:\n{result}"
            
        except Exception as e:
            logger.error(f"Error mapping article {article.url}: {e}")
            return None

    async def _reduce_summaries(self, map_results: List[str], candidate: CandidateHit) -> str:
        """
        Reduce Step: Synthesizes all extracted facts into a final report.
        """
        # Filter out None values (articles that were NO_MATCH or failed)
        valid_results = [res for res in map_results if res]
        
        if not valid_results:
            return f"### Screening Summary\n\nNo relevant adverse media was found for candidate **{candidate.entity_name}** across the provided event links."
            
        combined_facts = "\n\n".join(valid_results)
        
        prompt = f"""
        You are a senior compliance officer writing a Namelist Screening Event Summary.
        Synthesize the following extracted facts into a cohesive, professional markdown report for the candidate: {candidate.entity_name} (ID: {candidate.candidate_id}).
        
        Structure the report as follows:
        1. **Executive Summary** (2-3 sentences max)
        2. **Key Adverse Findings** (Bulleted list, deduplicate information across sources)
        3. **Source References**
        
        Extracted Facts:
        {combined_facts}
        """
        
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.reduce_model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2)
            )
            return response.text
        except Exception as e:
            logger.error(f"Error in reduce step: {e}")
            return "Error generating final summary. Please check system logs."

    async def generate_report(self, candidate: CandidateHit, articles: List[ScrapedArticle]) -> str:
        """
        The main public method that orchestrates the Map-Reduce pipeline.
        """
        logger.info(f"Starting Map-Reduce for {candidate.entity_name} over {len(articles)} articles.")
        
        # 1. MAP STEP (Run all extractions simultaneously)
        map_tasks = [self._map_article(article, candidate.entity_name) for article in articles]
        map_results = await asyncio.gather(*map_tasks)
        
        # 2. REDUCE STEP (Synthesize the final report)
        final_report = await self._reduce_summaries(map_results, candidate)
        
        return final_report
