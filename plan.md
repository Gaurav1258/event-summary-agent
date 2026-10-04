# Project Plan: Event Summary Agent

## Objective
Build an agent to assist investigators in Namelist Screening by automatically summarizing event links (news articles, list entries, etc.) associated with screening engine hits. A single candidate can have up to 100 associated events.

## Phases

### Phase 1: Foundation & Setup
- [x] Repository setup and structure.
- [x] `uv` virtual environment initialization.
- [x] Initial documentation (`README.md`, `plan.md`).

### Phase 1.5: Dataset Curation & Test Data Generation
- [x] Review and process open-source datasets to simulate Namelist Screening engine outputs.
  - *Adverse Media:* [Kaggle ADM Dataset](https://www.kaggle.com/datasets/gevaran/adverse-media-news-dataset-repository)
  - *Sanctions Entities:* [Alerterra Sanctions Entities](https://huggingface.co/datasets/alerterra/sanctions_entities)
  - *Match/False Positive Data:* [Usman Sanctions Match](https://huggingface.co/datasets/316usman/sanctions-screening-match), [OpenSanctions Pairs](https://huggingface.co/datasets/sanctions-er-anon/opensanctions_pairs)
  - *Reference Implementation:* [Adverse Media Screening Agent](https://github.com/afarinizadi/adverse-media-screening)
- [x] Write scripts to fetch/synthesize "mock hits" for local testing.

### Phase 2: Data Ingestion & Content Extraction
- [x] **Google Cloud Storage Integration:** Setup GCP Bucket and write scripts to host and fetch adverse media datasets remotely.
- [x] Define the input data schema (Candidate details, Hit context, List of URLs/Events) using Pydantic.
- [x] Implement a robust web scraper/content extractor to fetch text from various link types using `trafilatura`.
- [x] Handle request failures, timeouts, anti-bot protections, and rate limits gracefully.
- [x] Implement parallel/async processing to efficiently handle up to 100 links at once using `httpx` and `asyncio`.

### Phase 3: Summarization Engine (LLM Integration)
- [x] **Vertex AI Setup:** Install Google GenAI SDK and authenticate with `mlops2215` project using Gemini 2.5 Flash and Pro.
- [x] **Map Step (Parallel Extraction):** Design prompt to extract candidate-specific facts from individual articles concurrently.
- [x] **Reduce Step (Final Report):** Design synthesis prompt that generates final investigator summary report.
- [x] Implement the Map-Reduce orchestration logic in Python (`src/llm.py`).
- [x] **Evaluation Framework:** Create automated golden evalset (`tests/eval_data.json`) and pytest test suite (`tests/test_llm_eval.py`).

### Phase 3.5: Dynamic Threshold & Concurrency Optimization
- [x] **Direct Mode Threshold (`<= 3` links):** Route small requests to single unified Gemini 2.5 Pro prompt to minimize latency and token overhead.
- [x] **Map-Reduce Mode (`> 3` links):** Trigger parallel map extraction with Gemini 2.5 Flash for high-volume hits.
- [x] **Rate-Limit Throttle:** Apply `asyncio.Semaphore(10)` to map calls to prevent GCP 429 quota exhaustion on up to 100 links.
- [x] **Hierarchical Reduce:** Chunk combined facts when exceeding 25,000 characters before final synthesis.

### Phase 4: API & Backend Service
- [x] Develop a backend API (`src/api.py`) using FastAPI with CORS, logging, and error handling.
- [x] Define standardized JSON schemas (`src/schema.py`) with Pydantic for screening requests and responses.
- [x] Add `/health` monitoring endpoint.
- [x] Create comprehensive automated integration tests (`tests/test_api.py`) covering health, empty payloads, and live end-to-end Map-Reduce processing.

### Phase 5: GCP Infrastructure & Deployment
- [x] Set up GCP Project, Authentication, and IAM roles (`mlops2215`).
- [x] Containerize the application using Docker (`Dockerfile`, `.dockerignore`) using official UV base image.
- [x] **CI/CD Configuration:** Write `cloudbuild.yaml` for automated container builds and Cloud Run deployment.
- [x] Connect GitHub repo to Google Cloud Build triggers and deploy live.
- [x] Deploy live to Google Cloud Run (`https://event-summary-agent-vu53wmoyqa-uc.a.run.app`).
- [x] Implement proper logging and monitoring for auditing and debugging (Cloud Logging).
