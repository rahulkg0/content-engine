from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.database.database import init_db, get_db
from app.models.models import ContentBatch, ContentJob, JobStatus
from app.api.routes import batches, jobs, articles, websites

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto init database schema
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Production AI Content Automation Engine - Phase 1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(batches.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(articles.router, prefix=settings.API_V1_STR)
app.include_router(websites.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "demo_mode": settings.DEMO_MODE,
        "docs_url": "/docs"
    }

@app.get(f"{settings.API_V1_STR}/metrics")
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    batches_count = (await db.execute(select(func.count(ContentBatch.id)))).scalar() or 0
    jobs_count = (await db.execute(select(func.count(ContentJob.id)))).scalar() or 0

    researching_count = (await db.execute(
        select(func.count(ContentJob.id)).where(ContentJob.status.in_([JobStatus.RESEARCHING, JobStatus.BRIEF_GENERATING]))
    )).scalar() or 0

    writing_count = (await db.execute(
        select(func.count(ContentJob.id)).where(ContentJob.status.in_([JobStatus.WRITING, JobStatus.QUALITY_CHECK, JobStatus.REVISION_REQUIRED]))
    )).scalar() or 0

    review_count = (await db.execute(
        select(func.count(ContentJob.id)).where(ContentJob.status == JobStatus.AWAITING_APPROVAL)
    )).scalar() or 0

    published_count = (await db.execute(
        select(func.count(ContentJob.id)).where(ContentJob.status == JobStatus.PUBLISHED)
    )).scalar() or 0

    failed_count = (await db.execute(
        select(func.count(ContentJob.id)).where(ContentJob.status == JobStatus.FAILED)
    )).scalar() or 0

    return {
        "total_batches": batches_count,
        "total_articles": jobs_count,
        "pipeline": {
            "queued": jobs_count - (researching_count + writing_count + review_count + published_count + failed_count),
            "researching": researching_count,
            "writing": writing_count,
            "awaiting_review": review_count,
            "published": published_count,
            "failed": failed_count
        }
    }
