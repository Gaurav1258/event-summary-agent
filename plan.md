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
- [ ] **Vertex AI Setup:** Install Google GenAI SDK and authenticate with `mlops2215` project.
- [ ] **Map Step (Parallel Extraction):** Design a prompt to extract candidate-specific facts from individual articles concurrently.
- [ ] **Reduce Step (Final Report):** Design a synthesis prompt that takes the extracted facts and generates a final investigator summary.
- [ ] Implement the Map-Reduce orchestration logic in Python to tie the scraper outputs to the LLM inputs.

### Phase 4: API & Backend Service
- [ ] Develop a backend API (e.g., using FastAPI) to receive screening events and return summaries.
- [ ] Implement asynchronous task queues (e.g., using GCP Pub/Sub or Celery) since fetching and summarizing 100 links might take longer than standard HTTP timeout limits.
- [ ] Define standardized JSON response formats for the screening tools to ingest.

### Phase 5: GCP Infrastructure & Deployment
- [ ] Set up GCP Project, Authentication, and IAM roles.
- [ ] Containerize the application using Docker.
- [ ] **CI/CD Configuration:** Connect GitHub repo to Google Cloud Build for automated deployments.
- [ ] Deploy the API to Google Cloud Run automatically via Cloud Build.
- [ ] Implement proper logging and monitoring for auditing and debugging (Cloud Logging).
