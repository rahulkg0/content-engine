import json
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel


from app.database.database import get_db
from app.models.models import ContentBatch, ContentJob, JobStatus, BatchStatus
from app.services.csv_service import CSVService
from app.services.markdown_service import MarkdownService
from app.workers.content_tasks import process_content_job_task

router = APIRouter(prefix="/batches", tags=["Batches"])

class ValidateBatchRequest(BaseModel):
    headers: List[str]
    rows: List[Dict[str, str]]
    column_mapping: Dict[str, str]

class ConfirmBatchRequest(BaseModel):
    filename: str
    headers: List[str]
    rows: List[Dict[str, str]]
    column_mapping: Dict[str, str]

@router.post("/parse")
async def parse_csv_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are supported.")
    
    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("latin-1")

    headers, data_rows = CSVService.parse_csv_content(csv_text)
    if not headers or not data_rows:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty or missing headers.")

    detected_mapping = CSVService.auto_detect_mapping(headers)
    preview = CSVService.validate_and_preview(headers, data_rows, detected_mapping)

    return {
        "filename": file.filename,
        "headers": headers,
        "total_rows": len(data_rows),
        "detected_mapping": detected_mapping,
        "rows": data_rows,
        "preview": preview
    }

@router.post("/validate")
async def validate_csv_mapping(req: ValidateBatchRequest):
    preview = CSVService.validate_and_preview(req.headers, req.rows, req.column_mapping)
    return preview

def run_job_in_background(job_id: str):
    try:
        process_content_job_task(job_id)
    except Exception as e:
        print(f"Background task execution error for job {job_id}: {e}")

@router.post("/create")
async def create_batch_and_jobs(
    req: ConfirmBatchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    preview = CSVService.validate_and_preview(req.headers, req.rows, req.column_mapping)
    valid_rows = [r for r in preview["rows"] if r["is_valid"]]

    if not valid_rows:
        raise HTTPException(status_code=400, detail="No valid rows found to import.")

    # Create ContentBatch
    batch = ContentBatch(
        filename=req.filename,
        total_rows=preview["total_rows"],
        valid_rows=len(valid_rows),
        invalid_rows=preview["invalid_rows_count"],
        status=BatchStatus.PROCESSING
    )
    db.add(batch)
    await db.flush()

    jobs_created = []
    for row in valid_rows:
        job = ContentJob(
            batch_id=batch.id,
            topic=row["topic"],
            primary_keyword=row["primary_keyword"],
            search_volume=row.get("search_volume"),
            keyword_difficulty=row.get("keyword_difficulty"),
            target_density=row.get("target_density"),
            category=row.get("category"),
            audience=row.get("audience"),
            notes=row.get("notes"),
            status=JobStatus.QUEUED,
            current_step="QUEUED"
        )
        db.add(job)
        await db.flush()
        jobs_created.append(job)

    await db.commit()

    # Queue non-blocking background task execution for every valid job
    for job in jobs_created:
        background_tasks.add_task(run_job_in_background, job.id)

    return {
        "batch_id": batch.id,
        "filename": batch.filename,
        "total_rows": batch.total_rows,
        "valid_rows": batch.valid_rows,
        "jobs_count": len(jobs_created),
        "status": batch.status.value,
        "message": f"Successfully created batch with {len(jobs_created)} content jobs queued."
    }


@router.get("")
async def list_batches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentBatch).order_by(ContentBatch.created_at.desc()))
    batches = result.scalars().all()
    
    output = []
    for b in batches:
        # count job statuses
        jobs_res = await db.execute(select(ContentJob).where(ContentJob.batch_id == b.id))
        jobs = jobs_res.scalars().all()
        published_count = sum(1 for j in jobs if j.status == JobStatus.PUBLISHED)
        failed_count = sum(1 for j in jobs if j.status == JobStatus.FAILED)
        review_count = sum(1 for j in jobs if j.status == JobStatus.AWAITING_APPROVAL)
        processing_count = sum(1 for j in jobs if j.status not in [JobStatus.PUBLISHED, JobStatus.FAILED, JobStatus.AWAITING_APPROVAL, JobStatus.QUEUED])
        
        output.append({
            "id": b.id,
            "filename": b.filename,
            "total_rows": b.total_rows,
            "valid_rows": b.valid_rows,
            "invalid_rows": b.invalid_rows,
            "status": b.status.value,
            "created_at": (b.created_at.isoformat() + "Z") if b.created_at else None,
            "metrics": {
                "published": published_count,
                "failed": failed_count,
                "awaiting_review": review_count,
                "processing": processing_count
            }
        })
    return output

@router.get("/{batch_id}")
async def get_batch_detail(batch_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentBatch).where(ContentBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    jobs_res = await db.execute(select(ContentJob).where(ContentJob.batch_id == batch_id).order_by(ContentJob.created_at.asc()))
    jobs = jobs_res.scalars().all()

    jobs_list = []
    for j in jobs:
        jobs_list.append({
            "id": j.id,
            "topic": j.topic,
            "primary_keyword": j.primary_keyword,
            "search_volume": j.search_volume,
            "keyword_difficulty": j.keyword_difficulty,
            "target_density": j.target_density,
            "status": j.status.value,
            "current_step": j.current_step,
            "created_at": (j.created_at.isoformat() + "Z") if j.created_at else None
        })

    return {
        "id": batch.id,
        "filename": batch.filename,
        "total_rows": batch.total_rows,
        "valid_rows": batch.valid_rows,
        "invalid_rows": batch.invalid_rows,
        "status": batch.status.value,
        "created_at": (batch.created_at.isoformat() + "Z") if batch.created_at else None,
        "jobs": jobs_list
    }


@router.delete("/{batch_id}")
async def delete_batch(batch_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ContentBatch).where(ContentBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Fetch associated jobs to delete local temporary Markdown files
    jobs_res = await db.execute(select(ContentJob).where(ContentJob.batch_id == batch_id))
    jobs = jobs_res.scalars().all()
    for j in jobs:
        MarkdownService.delete_job_files(j.id)

    # Delete batch (cascade deletes ContentJob, Article, ArticleVersion, ActivityLog, PublishingJob)
    await db.delete(batch)
    await db.commit()

    return {
        "batch_id": batch_id,
        "message": f"Batch '{batch.filename}' and all associated jobs deleted successfully."
    }


@router.post("/{batch_id}/resume")
async def resume_batch(
    batch_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ContentBatch).where(ContentBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    jobs_res = await db.execute(select(ContentJob).where(ContentJob.batch_id == batch_id))
    jobs = jobs_res.scalars().all()

    # Find jobs that can be resumed: non-terminal or failed states
    resumable_statuses = [
        JobStatus.QUEUED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
        JobStatus.RESEARCHING,
        JobStatus.BRIEF_GENERATING,
        JobStatus.WRITING,
        JobStatus.QUALITY_CHECK
    ]

    resumed_jobs = []
    for j in jobs:
        if j.status in resumable_statuses:
            j.status = JobStatus.QUEUED
            j.current_step = "QUEUED"
            resumed_jobs.append(j)

    if not resumed_jobs:
        return {
            "batch_id": batch_id,
            "resumed_jobs_count": 0,
            "message": "No queued or failed jobs to resume in this batch."
        }

    batch.status = BatchStatus.PROCESSING
    await db.commit()

    # Trigger background execution for all resumed jobs
    for j in resumed_jobs:
        background_tasks.add_task(run_job_in_background, j.id)

    return {
        "batch_id": batch_id,
        "resumed_jobs_count": len(resumed_jobs),
        "message": f"Resumed processing for {len(resumed_jobs)} jobs in batch '{batch.filename}'."
    }

