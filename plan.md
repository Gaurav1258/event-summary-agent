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
- [ ] **Google Cloud Storage Integration:** Setup GCP Bucket and write scripts to host and fetch adverse media datasets remotely.
- [ ] Define the input data schema (Candidate details, Hit context, List of URLs/Events).
- [ ] Implement a robust web scraper/content extractor to fetch text from various link types (news articles, databases).
- [ ] Handle request failures, timeouts, anti-bot protections, and rate limits gracefully.
- [ ] Implement parallel/async processing to efficiently handle up to 100 links at once.

### Phase 3: Summarization Engine (LLM Integration)
- [ ] Integrate with GCP LLM services (e.g., Vertex AI / Gemini).
- [ ] Design and test prompts to generate concise, relevant summaries from the extracted text that focus on answering investigator needs (determining match likelihood).
- [ ] Implement a strategy for handling large context windows (e.g., Map-Reduce or iterative summarization) if the combined text of 100 links exceeds token limits.

### Phase 4: API & Backend Service
- [ ] Develop a backend API (e.g., using FastAPI) to receive screening events and return summaries.
- [ ] Implement asynchronous task queues (e.g., using GCP Pub/Sub or Celery) since fetching and summarizing 100 links might take longer than standard HTTP timeout limits.
- [ ] Define standardized JSON response formats for the screening tools to ingest.

### Phase 5: GCP Infrastructure & Deployment
- [ ] Set up GCP Project, Authentication, and IAM roles.
- [ ] Containerize the application using Docker.
- [ ] Deploy the API (e.g., to Google Cloud Run).
- [ ] Implement proper logging and monitoring for auditing and debugging (Cloud Logging).
