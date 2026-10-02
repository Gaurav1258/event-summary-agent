# Event Summary Agent

## Overview
The **Event Summary Agent** is designed to streamline the workflow of investigators during Namelist Screening operations. When a screening engine generates a hit against a candidate, it often flags numerous associated links or "events" (such as news articles, list entries, etc.) that the investigator must review. 

With candidates potentially having up to 100 event links attached to a hit, manual review is a significant bottleneck. This agent automatically fetches the content from these links and generates a cohesive, actionable summary. This empowers investigators to quickly and accurately decide if a candidate truly matches the hit without having to open and read dozens of articles manually.

## Key Features
* **Automated Content Extraction:** Asynchronously fetches and extracts text from a wide variety of external event links.
* **Intelligent Summarization:** Utilizes Large Language Models (via GCP) to synthesize information across multiple sources into a single, concise summary tailored for compliance and screening.
* **High-Volume Handling:** Designed to scale and process up to 100 events per candidate efficiently.

## Getting Started

### Prerequisites
* [uv](https://github.com/astral-sh/uv) for dependency management and fast environment resolution.

### Installation & Setup
1. Clone the repository.
2. The environment is managed via `uv`. Activate the virtual environment:
   ```bash
   # On Windows
   .venv\Scripts\activate
   ```
3. Install dependencies (once added):
   ```bash
   uv sync
   ```

## Development Roadmap
Please refer to [plan.md](plan.md) for detailed development phases, architecture plans, and task tracking.
