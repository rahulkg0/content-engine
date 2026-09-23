from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database.database import get_db
from app.models.models import ContentJob, ActivityLog, PublishingJob, JobStatus
from app.services.markdown_service import MarkdownService
from app.workers.content_tasks import process_content_job_task, publish_to_strapi_task, regenerate_job_step_task, force_finalize_job_task, revise_content_job_task

class RegenerateStepRequest(BaseModel):
    step_filename: str

def safe_regenerate_step_task(job_id: str, step_filename: str):
    try:
        regenerate_job_step_task(job_id, step_filename)
    except Exception as e:
        print(f"Error regenerating step {step_filename} for job {job_id}: {e}")

def safe_force_finalize_task(job_id: str):
    try:
        force_finalize_job_task(job_id)
    except Exception as e:
        print(f"Error force finalizing job {job_id}: {e}")

def safe_revise_task(job_id: str):
    try:
        revise_content_job_task(job_id)
    except Exception as e:
        print(f"Error revising job {job_id}: {e}")

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def safe_process_task(job_id: str):
    try:
        process_content_job_task(job_id)
    except Exception as e:
        print(f"Error processing job {job_id}: {e}")

def safe_publish_task(job_id: str):
    try:
        publish_to_strapi_task(job_id)
    except Exception as e:
        print(f"Error publishing job {job_id}: {e}")

@router.get("/{job_id}")
async def get_job_detail(job_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ContentJob).where(ContentJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Publishing job if present
    pub_res = await db.execute(select(PublishingJob).where(PublishingJob.content_job_id == job_id))
    pub = pub_res.scalar_one_or_none()

    files = MarkdownService.get_all_job_files(job_id)

    return {
        "id": job.id,
        "batch_id": job.batch_id,
        "topic": job.topic,
        "primary_keyword": job.primary_keyword,
        "search_volume": job.search_volume,
        "keyword_difficulty": job.keyword_difficulty,
        "target_density": job.target_density,
        "category": job.category,
        "audience": job.audience,
        "notes": job.notes,
        "status": job.status.value,
        "current_step": job.current_step,
        "retry_count": job.retry_count,
        "created_at": (job.created_at.isoformat() + "Z") if job.created_at else None,
        "updated_at": (job.updated_at.isoformat() + "Z") if job.updated_at else None,
        "markdown_files": files,
        "publishing_info": {
            "cms_entry_id": pub.cms_entry_id if pub else None,
            "published_url": pub.published_url if pub else None,
            "status": pub.status if pub else None,
            "error_message": pub.error_message if pub else None,
            "published_at": (pub.published_at.isoformat() + "Z") if pub and pub.published_at else None
        }
    }

@router.get("/{job_id}/files")
async def get_job_files_status(job_id: str):
    return MarkdownService.get_all_job_files(job_id)

@router.get("/{job_id}/files/{filename}")
async def preview_job_file(job_id: str, filename: str):
    if (".." in filename) or ("/" in filename) or ("\\" in filename) or not (filename.endswith(".md") or filename.endswith(".json")):
        raise HTTPException(status_code=400, detail="Invalid filename requested.")

    content = MarkdownService.read_markdown(job_id, filename)
    if content is None:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found for job {job_id}.")

    return {"filename": filename, "content": content}

@router.get("/{job_id}/activity")
async def get_job_activity_log(job_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(ActivityLog).where(ActivityLog.content_job_id == job_id).order_by(ActivityLog.timestamp.asc())
    )
    logs = res.scalars().all()
    return [
        {
            "id": log.id,
            "step_name": log.step_name,
            "status": log.status,
            "message": log.message,
            "timestamp": (log.timestamp.isoformat() + "Z") if log.timestamp else None
        } for log in logs
    ]

@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(ContentJob).where(ContentJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.QUEUED
    job.current_step = "QUEUED_RETRY"
    job.retry_count += 1
    await db.commit()

    background_tasks.add_task(safe_process_task, job_id)

    return {"message": "Job queued for retry processing."}

@router.post("/{job_id}/publish-retry")
async def retry_publishing(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(ContentJob).where(ContentJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.APPROVED
    job.current_step = "RETRY_PUBLISHING"
    await db.commit()

    background_tasks.add_task(safe_publish_task, job_id)

    return {"message": "Publishing job queued for retry."}


@router.post("/{job_id}/regenerate-step")
async def regenerate_job_step(
    job_id: str,
    req: RegenerateStepRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(ContentJob).where(ContentJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    background_tasks.add_task(safe_regenerate_step_task, job_id, req.step_filename)

    return {
        "job_id": job_id,
        "step_filename": req.step_filename,
        "message": f"Step '{req.step_filename}' regeneration queued successfully."
    }


@router.post("/{job_id}/force-finalize")
async def force_finalize_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(ContentJob).where(ContentJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    background_tasks.add_task(safe_force_finalize_task, job_id)

    return {
        "job_id": job_id,
        "message": "Force finalization task queued. 05-final.md will be generated and routed to Human Review."
    }


@router.post("/{job_id}/revise")
async def revise_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(ContentJob).where(ContentJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.WRITING
    job.current_step = "REVISING"
    await db.commit()

    background_tasks.add_task(safe_revise_task, job_id)

    return {
        "job_id": job_id,
        "message": "Draft revision task queued successfully."
    }




