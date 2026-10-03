import os
import sys
import json
import pytest
from dotenv import load_dotenv

# Ensure Python can find our 'src' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.schema import ScrapedArticle
from src.llm import SummarizationEngine

# Load environment variables for GCP authentication
load_dotenv()

@pytest.fixture
def engine():
    project_id = os.environ.get("GCP_PROJECT_ID", "mlops2215")
    # We initialize the engine just like in production
    return SummarizationEngine(project_id=project_id)

@pytest.mark.asyncio
async def test_map_prompt_accuracy(engine):
    """
    Evaluates the Map prompt against our golden evalset to ensure it correctly
    identifies matches, ignores false positives, and extracts key facts.
    """
    eval_file_path = os.path.join(os.path.dirname(__file__), "eval_data.json")
    with open(eval_file_path, "r") as f:
        eval_cases = json.load(f)
        
    for case in eval_cases:
        print(f"\nEvaluating: {case['test_id']} - {case['description']}")
        
        # Create a mock article with the test text
        article = ScrapedArticle(url="https://eval-test.com", content=case["article_text"])
        
        # Run the LLM prompt
        result = await engine._map_article(article, case["candidate_name"])
        
        # Check against expected outcomes
        if case["expected_result"] == "NO_MATCH":
            assert result is None, f"FAIL {case['test_id']}: LLM falsely flagged an innocent article! Output: {result}"
            print("[PASS] Correctly ignored false positive / unrelated article.")
        else:
            assert result is not None, f"FAIL {case['test_id']}: LLM missed a true positive match!"
            
            # Verify the LLM successfully extracted the critical facts
            lower_result = result.lower()
            for kw in case["expected_keywords"]:
                assert kw.lower() in lower_result, f"FAIL {case['test_id']}: LLM missed critical keyword '{kw}'. Output: {result}"
                
            print("[PASS] Correctly identified match and extracted all key facts.")
