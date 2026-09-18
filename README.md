# ContentEngine — CSV-Driven AI Content Automation System (Phase 1)

Production-oriented, modular, resumable AI-powered content automation platform. Ingests CSV files of blog topics and SEO metadata, researches each topic, executes a multi-stage LangGraph AI workflow, creates five temporary Markdown files per article (`01-research.md` through `05-final.md`), provides a human review interface, sends approved content to Strapi CMS, verifies publication, and deletes temporary files only upon confirmed publication.

---

## Architecture Overview

```
CSV Upload → Validation & Mapping → Create Batch & ContentJobs
                                            ↓
                                   Redis Task Queue
                                            ↓
                                  Celery Worker Cluster
                                            ↓
                                LangGraph Agent Workflow
  ┌───────────────────────────────────────────────────────────────────────────┐
  │ Research Agent (01-research.md) → Content Strategist (02-content-brief.md) │
  │        ↓                                                                  │
  │ Writer Agent (03-draft.md) ← Revision Loop (max 3 retries)                │
  │        ↓                                                                  │
  │ Quality Audit: Fact Check + SEO + Editorial (04-quality-seo.md)           │
  │        ↓                                                                  │
  │ Clean Final Article Generation (05-final.md)                             │
  └───────────────────────────────────────────────────────────────────────────┘
                                            ↓
                               Human Approval Queue (/review)
                                            ↓
                                 Strapi Publisher API
                                            ↓
                           Verify Strapi HTTP 200 & Entry ID
                                            ↓
                        Delete 01-05 Temporary Markdown Files
                                            ↓
                              Mark Job Status: PUBLISHED
```

---

## Prerequisites

- **Docker & Docker Compose** (Recommended for full stack execution)
- **Node.js** v18+ (For frontend Next.js application)
- **Python** 3.11+ (For FastAPI backend & Celery workers)
- **Redis** server (For background task queue)
- **PostgreSQL** with `pgvector` extension (Or SQLite for quick local demo)

---

## Quick Start with Docker Compose

To launch the complete infrastructure (PostgreSQL, Redis, FastAPI Backend, Celery Worker, Next.js Frontend):

```bash
cd content-engine
docker-compose up --build
```

Access the UI at [http://localhost:3000](http://localhost:3000)  
Access the Backend API Docs at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Local Development Setup (Manual)

### 1. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Set key credentials:
- `OPENROUTER_API_KEY`: OpenRouter key for live AI completions (Optional, fallback to DEMO mode if blank)
- `STRAPI_URL`: Base URL for Strapi CMS (Default: `http://localhost:1337`)
- `STRAPI_API_TOKEN`: Strapi bearer token for publishing
- `DEMO_MODE`: Set to `true` to run locally without external credentials.

### 2. FastAPI Backend Setup

```bash
cd content-engine/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Celery Worker Setup

In a separate terminal tab:

```bash
cd content-engine/backend
source venv/bin/activate
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

### 4. Next.js Frontend Setup

In a separate terminal tab:

```bash
cd content-engine/frontend
npm install
npm run dev
```

---

## Example CSV Format

Create a CSV file (e.g. `topics.csv`) with the following headers:

```csv
Blog topic,Primary keyword,Vol.,KD,Target density
Career Options: How to Choose the Right Career Path,career options,4400,35,0.8–1.0%
Career Opportunities in India: Best Paths for Students & Graduates,career opportunities,18100,57,0.7–0.9%
Career Jobs: How to Find the Right Job for Your Skills,career jobs,9900,37,0.8–1.0%
```

---

## Complete First Batch Demonstration Flow

1. Open `http://localhost:3000` in your browser.
2. Click **Upload New CSV** or navigate to `/batches/new`.
3. Select `topics.csv`.
4. Verify column auto-mapping (`Blog topic` -> `topic`, `Primary keyword` -> `primary_keyword`).
5. Inspect row validation preview (valid vs invalid vs duplicate rows).
6. Click **Import Topics** to confirm import and dispatch processing jobs.
7. Navigate to `/batches/[id]` to monitor real-time job progress bar.
8. Click any job to inspect the generated Markdown files (`01-research.md` through `05-final.md`).
9. Navigate to `/review` (Human Review Queue).
10. Click **Approve & Publish** for an article.
11. System posts content to Strapi, verifies publication ID, deletes temporary files, and marks status as `PUBLISHED`.

---

## Temporary File Integrity Guarantee

- Temporary Markdown files (`storage/jobs/{job_id}/01-research.md` ... `05-final.md`) are created during the agent workflow.
- **Strict Guardrail**: Markdown files are **NEVER** deleted if Strapi publication fails or is pending.
- In the event of a network or CMS API error, files remain intact for instant retry without re-spending AI tokens.
- Safe deletion is executed only after Strapi confirms HTTP 2xx and returns a valid entry ID.

---

## Troubleshooting

- **Celery Broker Connection Error**: Ensure Redis server is running on `localhost:6379`.
- **Database Schema Sync**: Backend automatically runs `init_db()` on FastAPI startup.
- **DEMO Mode Switch**: Toggle DEMO mode on `/settings` or in `.env` (`DEMO_MODE=true`).
