import asyncio
import logging
from typing import List, Optional
from google import genai
from google.genai import types

from .schema import CandidateHit, ScrapedArticle

logger = logging.getLogger(__name__)

class SummarizationEngine:
    """
    Orchestrates adaptive LLM summarization using Google Vertex AI.
    Dynamically selects between Direct Mode (for <= 3 articles) and
    Throttled Map-Reduce (for > 3 articles) with Hierarchical Reduce support.
    """
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        max_concurrent_maps: int = 10,
        direct_threshold: int = 3,
        hierarchical_char_threshold: int = 25000
    ):
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        
        # Models
        self.map_model = "gemini-2.5-flash"
        self.reduce_model = "gemini-2.5-pro"
        
        # Concurrency & Threshold configuration
        self.map_semaphore = asyncio.Semaphore(max_concurrent_maps)
        self.direct_threshold = direct_threshold
        self.hierarchical_char_threshold = hierarchical_char_threshold

    async def _direct_summarize(self, articles: List[ScrapedArticle], candidate: CandidateHit) -> str:
        """
        Direct Mode: When there are 3 or fewer articles, synthesizes them in a single prompt
        using Gemini 2.5 Pro. Reduces latency and preserves cross-document reasoning.
        """
        logger.info(f"Executing Direct Mode for {len(articles)} articles on candidate {candidate.entity_name}.")
        
        articles_context = []
        for i, article in enumerate(articles, 1):
            articles_context.append(
                f"--- Article {i} [Source: {article.url}] ---\n{article.content[:20000]}"
            )
        combined_text = "\n\n".join(articles_context)
        
        prompt = f"""
        You are a senior compliance officer writing a Namelist Screening Event Summary.
        Analyze the following articles and determine if they contain adverse media or risk-relevant findings
        specifically regarding the candidate: '{candidate.entity_name}' (ID: {candidate.candidate_id}).
        
        CRITICAL RULES:
        - If none of the articles mention this candidate, or if mentions are false positives (unrelated person/business), state clearly that no relevant adverse media was found.
        - If there ARE adverse media or risk findings, structure your report as:
          1. **Executive Summary** (2-3 sentences max)
          2. **Key Adverse Findings** (Bulleted list of deduplicated allegations, investigations, sanctions, or crimes)
          3. **Source References** (List corresponding URLs)
        
        Articles:
        {combined_text}
        """
        
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.reduce_model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.15)
            )
            return response.text
        except Exception as e:
            logger.error(f"Error in direct summarization: {e}")
            return "Error generating direct summary. Please check system logs."

    async def _map_article(self, article: ScrapedArticle, candidate_name: str) -> Optional[str]:
        """
        Map Step: Analyzes a single article to extract adverse facts about the candidate.
        Throttled via self.map_semaphore to prevent GCP rate limits.
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
        
        async with self.map_semaphore:
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.map_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                result = response.text.strip()
                
                if "NO_MATCH" in result:
                    return None
                    
                return f"From {article.url}:\n{result}"
                
            except Exception as e:
                logger.error(f"Error mapping article {article.url}: {e}")
                return None

    async def _hierarchical_intermediate_reduce(self, chunk: List[str], candidate: CandidateHit) -> str:
        """Helper to reduce a batch of extracted facts during hierarchical reduction."""
        combined = "\n\n".join(chunk)
        prompt = f"""
        Synthesize and consolidate the following adverse media findings for candidate '{candidate.entity_name}'.
        Deduplicate points and retain key facts, dates, amounts, and source URLs:
        
        Findings:
        {combined}
        """
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.map_model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            return response.text
        except Exception as e:
            logger.error(f"Error in hierarchical batch: {e}")
            return combined

    async def _reduce_summaries(self, map_results: List[str], candidate: CandidateHit) -> str:
        """
        Reduce Step: Synthesizes all extracted facts into the final investigator report.
        Automatically applies hierarchical chunking if payload exceeds threshold.
        """
        valid_results = [res for res in map_results if res]
        
        if not valid_results:
            return f"### Screening Summary\n\nNo relevant adverse media was found for candidate **{candidate.entity_name}** across the provided event links."
            
        combined_facts = "\n\n".join(valid_results)
        
        # Check if facts are massive (e.g. from 50-100 articles) -> Apply Hierarchical Reduce
        if len(combined_facts) > self.hierarchical_char_threshold and len(valid_results) > 10:
            logger.info(f"Facts volume ({len(combined_facts)} chars) exceeds threshold. Applying hierarchical reduce.")
            chunk_size = 10
            chunks = [valid_results[i:i + chunk_size] for i in range(0, len(valid_results), chunk_size)]
            intermediate_tasks = [self._hierarchical_intermediate_reduce(chunk, candidate) for chunk in chunks]
            intermediate_summaries = await asyncio.gather(*intermediate_tasks)
            combined_facts = "\n\n".join(intermediate_summaries)

        prompt = f"""
        You are a senior compliance officer writing a Namelist Screening Event Summary.
        Synthesize the following extracted facts into a cohesive, professional markdown report for the candidate: {candidate.entity_name} (ID: {candidate.candidate_id}).
        
        Structure the report as follows:
        1. **Executive Summary** (2-3 sentences max)
        2. **Key Adverse Findings** (Bulleted list, deduplicate information across sources)
        3. **Source References** (Bulleted list of cited URLs)
        
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
            logger.error(f"Error in final reduce step: {e}")
            return "Error generating final summary. Please check system logs."

    async def generate_report(self, candidate: CandidateHit, articles: List[ScrapedArticle]) -> str:
        """
        Entry point: Dynamically routes between Direct Mode (<= 3 articles)
        and Throttled Map-Reduce (> 3 articles).
        """
        successful_articles = [a for a in articles if a.is_success]
        
        if not successful_articles:
            return f"### Screening Summary\n\nUnable to extract content from any of the provided event links for **{candidate.entity_name}**."
            
        # DYNAMIC THRESHOLD CHECK:
        if len(successful_articles) <= self.direct_threshold:
            logger.info(f"Hit has {len(successful_articles)} valid articles (<= {self.direct_threshold}). Routing to DIRECT MODE.")
            return await self._direct_summarize(successful_articles, candidate)
        else:
            logger.info(f"Hit has {len(successful_articles)} valid articles (> {self.direct_threshold}). Routing to MAP-REDUCE MODE.")
            map_tasks = [self._map_article(article, candidate.entity_name) for article in successful_articles]
            map_results = await asyncio.gather(*map_tasks)
            return await self._reduce_summaries(map_results, candidate)

