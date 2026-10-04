# Implementation Architecture & Data Flow

This document outlines the exact data flow and architectural components of the Event Summary Agent. By separating the UI, API, Scraper, and LLM orchestration, we ensure a highly scalable and resilient system.

## System Architecture Diagram

```mermaid
flowchart TD
    %% External Entities
    UI[Investigator UI or Screening Engine]
    MCP[MCP Server or API Client]
    
    %% Backend Service (Cloud Run)
    subgraph Backend [Google Cloud Run FastAPI Service]
        API[FastAPI Endpoint POST api summarize]
        Orchestrator[Map-Reduce Orchestrator src llm.py]
        Scraper[Async Web Scraper src scraper.py]
    end
    
    %% GCP Services
    GCS[(Google Cloud Storage Mock Data)]
    VertexAI[Google Vertex AI Gemini Models]
    
    %% Data Flow
    UI -->|1. Candidate Profile and Hit Metadata| MCP
    MCP -->|2. HTTP POST URLs and Candidate Info| API
    API -->|3. Validates payload via Pydantic| Orchestrator
    
    %% Fetching Data
    Orchestrator -->|4. List of up to 100 URLs| Scraper
    Scraper -->|5. Async HTTP GET| ExternalWeb[External News Sites]
    ExternalWeb -->|6. Raw HTML| Scraper
    Scraper -->|7. Cleaned Text| Orchestrator
    
    %% Note: GCS is used for testing mock data instead of External Web
    GCS -.->|Alternative Fetch Test Data| Orchestrator
    
    %% LLM Map-Reduce Flow
    Orchestrator -->|8. Parallel Prompts Map Step| VertexAI
    VertexAI -->|9. Up to 100 Fact Extractions| Orchestrator
    Orchestrator -->|10. Final Synthesis Prompt Reduce Step| VertexAI
    VertexAI -->|11. Final Investigator Report| Orchestrator
    
    %% Return Path
    Orchestrator -->|12. Final Report Object| API
    API -->|13. JSON Response| MCP
    MCP -->|14. Formatted Display| UI
```

## Component Breakdown

### 1. The Client (MCP / Screening Engine / UI)
- **What it gets (Input):** Raw screening engine hits (Candidate details + Event URLs).
- **What it gives (Output):** Sends a structured JSON payload (`CandidateHit`) to the FastAPI backend.
- **What it expects back:** A structured JSON response containing the final synthesized markdown report, which the UI/MCP will render for the investigator.

### 2. FastAPI Endpoint (`src/api.py`)
- **What it gets:** The HTTP POST request from the MCP client.
- **What it does:** Uses `src/schema.py` to validate that the URLs are properly formatted and the candidate data is present. It acts purely as a router, handing the validated object to the Orchestrator.
- **What it gives:** An HTTP 200 JSON response containing the final summary, or HTTP 400/500 errors if validation or processing fails.

### 3. Async Web Scraper (`src/scraper.py`)
- **What it gets:** A list of raw `EventLink` URLs.
- **What it does:** Visits the URLs concurrently (with a semaphore to limit simultaneous connections to ~10). It strips away navigation bars, ads, and footers, extracting *only* the main article text.
- **What it gives:** A list of `ScrapedArticle` objects containing the clean text (or an error status if the URL was a 404).

### 4. Map-Reduce Orchestrator (`src/llm.py`)
- **What it gets:** The cleaned text from all successful `ScrapedArticle` objects.
- **What it does (Map Step):** Sends each article's text *individually* to Vertex AI. The prompt asks: *"Does this text mention the candidate? If so, extract the risk-relevant facts."*
- **What it does (Reduce Step):** Collects all the extracted facts from the Map step and sends them *together* to Vertex AI in a final prompt. This prompt asks the LLM to write a cohesive, deduplicated Investigator Summary.
- **What it gives:** The final text report back to the FastAPI endpoint.


## Dynamic Orchestration & Threshold Architecture

To optimize latency, cost, and rate limits, the summarization engine employs an adaptive orchestration strategy based on link count and payload volume:

```mermaid
flowchart TD
    Start[Incoming Candidate Hit] --> Check{Number of Valid Articles}
    Check -->|3 or Fewer Articles| Direct[Direct Mode: Single Gemini 2.5 Pro Call]
    Check -->|More than 3 Articles| Map[Map-Reduce Mode]
    
    subgraph Map-Reduce Mode
        Map --> ThrottledMap[Parallel Map Step: Semaphore 10 - Gemini 2.5 Flash]
        ThrottledMap --> Filter[Filter NO_MATCH articles]
        Filter --> CheckTokens{Combined Facts Length}
        CheckTokens -->|Standard Size: 25000 chars or less| FinalReduce[Final Synthesis Report: Gemini 2.5 Pro]
        CheckTokens -->|Exceeds 25000 chars| TreeReduce[Hierarchical Chunked Reduce]
        TreeReduce --> FinalReduce
    end
    
    Direct --> Output[Investigator Summary Report]
    FinalReduce --> Output
```

### Threshold Specifications

| Mode / Feature | Trigger Condition | Execution Strategy | Model Used |
| :--- | :--- | :--- | :--- |
| **Direct Mode** | `<= 3` valid articles | Skips Map extraction entirely. Sends all articles directly in a unified prompt for fast cross-document reasoning. | `gemini-2.5-pro` |
| **Map-Reduce Mode** | `> 3` valid articles | Executes parallel map extraction on each article to weed out false positives and isolate adverse facts. | `gemini-2.5-flash` |
| **Concurrency Throttle** | All Map operations | Uses `asyncio.Semaphore(10)` to cap concurrent Vertex AI API calls at 10 to avoid GCP 429 rate limits. | N/A (Async runtime) |
| **Hierarchical Reduce** | Combined facts `> 25,000` characters | Batches extracted facts into chunks of 10 for intermediate synthesis before generating the final report. | `gemini-2.5-pro` |
