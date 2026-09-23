import asyncio
from datetime import datetime
from app.workers.celery_app import celery_app
from app.database.database import SyncSessionLocal
from app.models.models import ContentJob, JobStatus, ActivityLog, PublishingJob, Article, ArticleVersion
from app.workflows.content_workflow import ContentWorkflow
from app.agents.research_agent import ResearchAgent
from app.agents.strategist_agent import StrategistAgent
from app.agents.writer_agent import WriterAgent
from app.agents.quality_agent import QualityAgent
from app.agents.revision_agent import RevisionAgent
from app.services.markdown_service import MarkdownService
from app.services.strapi_service import StrapiService
from app.config import settings


def log_activity_sync(db, job_id: str, step_name: str, status: str, message: str, details: dict = None):
    activity = ActivityLog(
        content_job_id=job_id,
        step_name=step_name,
        status=status,
        message=message,
        details=details or {}
    )
    db.add(activity)
    db.commit()

@celery_app.task(name="tasks.regenerate_job_step")
def regenerate_job_step_task(job_id: str, step_filename: str):
    db = SyncSessionLocal()
    job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
    if not job:
        db.close()
        return {"error": f"Job {job_id} not found."}

    try:
        job_data = {
            "topic": job.topic,
            "primary_keyword": job.primary_keyword,
            "search_volume": job.search_volume,
            "keyword_difficulty": job.keyword_difficulty,
            "target_density": job.target_density,
            "audience": job.audience
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        step_clean = step_filename.lower()
        if "01" in step_clean or "research" in step_clean:
            log_activity_sync(db, job_id, "REGENERATE_RESEARCH", "STARTED", "Regenerating research report (01-research.md)...")
            job.status = JobStatus.RESEARCHING
            job.current_step = "RESEARCHING"
            db.commit()
            loop.run_until_complete(ResearchAgent.run(job_id, job_data))
            log_activity_sync(db, job_id, "REGENERATE_RESEARCH", "SUCCESS", "Research report regenerated successfully.")

        elif "02" in step_clean or "brief" in step_clean:
            log_activity_sync(db, job_id, "REGENERATE_BRIEF", "STARTED", "Regenerating content brief (02-content-brief.md)...")
            job.status = JobStatus.BRIEF_GENERATING
            job.current_step = "BRIEF_GENERATING"
            db.commit()
            loop.run_until_complete(StrategistAgent.run(job_id, job_data))
            log_activity_sync(db, job_id, "REGENERATE_BRIEF", "SUCCESS", "Content brief regenerated successfully.")

        elif "03" in step_clean or "draft" in step_clean:
            log_activity_sync(db, job_id, "REGENERATE_DRAFT", "STARTED", "Regenerating draft article (03-draft.md)...")
            job.status = JobStatus.WRITING
            job.current_step = "WRITING"
            db.commit()
            loop.run_until_complete(WriterAgent.run(job_id, job_data))
            log_activity_sync(db, job_id, "REGENERATE_DRAFT", "SUCCESS", "Draft article regenerated successfully.")

        elif "04" in step_clean or "quality" in step_clean:
            log_activity_sync(db, job_id, "REGENERATE_QUALITY", "STARTED", "Regenerating quality audit (04-quality-seo.md)...")
            job.status = JobStatus.QUALITY_CHECK
            job.current_step = "QUALITY_CHECK"
            db.commit()
            passed, result_status, metrics = loop.run_until_complete(QualityAgent.evaluate_and_finalize(job_id, job_data, force_finalize=False))
            log_activity_sync(db, job_id, "REGENERATE_QUALITY", "SUCCESS" if passed else "FAILED", f"Quality audit complete. Result: {result_status}")

        elif "05" in step_clean or "final" in step_clean:
            log_activity_sync(db, job_id, "REGENERATE_FINAL", "STARTED", "Force-generating final article (05-final.md)...")
            job.status = JobStatus.QUALITY_CHECK
            job.current_step = "QUALITY_CHECK"
            db.commit()
            passed, result_status, metrics = loop.run_until_complete(QualityAgent.evaluate_and_finalize(job_id, job_data, force_finalize=True))
            log_activity_sync(db, job_id, "REGENERATE_FINAL", "SUCCESS", "05-final.md successfully generated and finalized.")

        loop.close()

        # Reset job state back to AWAITING_APPROVAL if final article exists
        if MarkdownService.read_markdown(job_id, "05-final.md"):
            job.status = JobStatus.AWAITING_APPROVAL
            job.current_step = "AWAITING_APPROVAL"
        else:
            job.status = JobStatus.DRAFT_COMPLETE
            job.current_step = "DRAFT_COMPLETE"

        db.commit()
        return {"job_id": job_id, "step": step_filename, "status": job.status.value}

    except Exception as e:
        db.rollback()
        job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            db.commit()
            log_activity_sync(db, job_id, "REGENERATE_ERROR", "FAILED", f"Regeneration failed for {step_filename}: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="tasks.force_finalize_job")
def force_finalize_job_task(job_id: str):
    db = SyncSessionLocal()
    job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
    if not job:
        db.close()
        return {"error": f"Job {job_id} not found."}

    try:
        job_data = {
            "topic": job.topic,
            "primary_keyword": job.primary_keyword,
            "search_volume": job.search_volume,
            "keyword_difficulty": job.keyword_difficulty,
            "target_density": job.target_density,
            "audience": job.audience
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        log_activity_sync(db, job_id, "FORCE_FINALIZE", "STARTED", "Force finalizing 05-final.md article from draft...")

        passed, result_status, metrics = loop.run_until_complete(
            QualityAgent.evaluate_and_finalize(job_id, job_data, force_finalize=True)
        )
        loop.close()

        final_article_text = MarkdownService.read_markdown(job_id, "05-final.md") or job.topic

        job.status = JobStatus.AWAITING_APPROVAL
        job.current_step = "AWAITING_APPROVAL"

        # Record or update Article in DB
        existing_art = db.query(Article).filter(Article.job_id == job_id).first()
        if not existing_art:
            art = Article(
                job_id=job_id,
                title=job.topic,
                slug=StrapiService.generate_slug(job.topic),
                current_version=1,
                status="AWAITING_APPROVAL"
            )
            db.add(art)
            db.flush()

            ver = ArticleVersion(
                article_id=art.id,
                version_number=1,
                content_body=final_article_text,
                change_summary="Force-finalized article version."
            )
            db.add(ver)

        log_activity_sync(db, job_id, "FORCE_FINALIZE", "SUCCESS", "05-final.md generated and job moved to Human Review (AWAITING_APPROVAL).")
        db.commit()
        return {"job_id": job_id, "status": "AWAITING_APPROVAL"}

    except Exception as e:
        db.rollback()
        log_activity_sync(db, job_id, "FORCE_FINALIZE_ERROR", "FAILED", f"Error during force finalize: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()



@celery_app.task(name="tasks.process_content_job")
def process_content_job_task(job_id: str):
    db = SyncSessionLocal()
    job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
    if not job:
        db.close()
        return {"error": f"Job {job_id} not found."}

    try:
        job.status = JobStatus.RESEARCHING
        job.current_step = "RESEARCHING"
        db.commit()
        log_activity_sync(db, job_id, "WORKFLOW_START", "STARTED", "Content pipeline initialized.")

        job_data = {
            "topic": job.topic,
            "primary_keyword": job.primary_keyword,
            "search_volume": job.search_volume,
            "keyword_difficulty": job.keyword_difficulty,
            "target_density": job.target_density,
            "audience": job.audience
        }

        # Run LangGraph pipeline synchronously via asyncio event loop
        graph = ContentWorkflow.build_graph()
        initial_state = {
            "job_id": job_id,
            "job_data": job_data,
            "status": "RESEARCHING",
            "current_step": "RESEARCHING",
            "retry_count": 0,
            "revision_notes": None,
            "error_message": None
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        final_state = loop.run_until_complete(graph.ainvoke(initial_state))
        loop.close()

        # Update database with final state
        job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
        final_status = final_state.get("status")
        if final_status == "AWAITING_APPROVAL":
            job.status = JobStatus.AWAITING_APPROVAL
            job.current_step = "AWAITING_APPROVAL"
            
            # Record Article in DB
            final_article_text = MarkdownService.read_markdown(job_id, "05-final.md") or job.topic
            article = Article(
                job_id=job_id,
                title=job.topic,
                slug=StrapiService.generate_slug(job.topic),
                current_version=1,
                status="AWAITING_APPROVAL"
            )
            db.add(article)
            db.flush()

            version = ArticleVersion(
                article_id=article.id,
                version_number=1,
                content_body=final_article_text,
                change_summary="Initial generated version passing quality checks."
            )
            db.add(version)
            log_activity_sync(db, job_id, "FINAL_READY", "SUCCESS", "Article passed quality checks and is awaiting approval.")
        elif final_status == "MANUAL_REVIEW_REQUIRED":
            job.status = JobStatus.MANUAL_REVIEW_REQUIRED
            job.current_step = "MANUAL_REVIEW_REQUIRED"
            log_activity_sync(
                db, job_id, "MANUAL_REVIEW_REQUIRED", "WARNING",
                final_state.get("error_message") or f"Quality checks failed after {settings.MAX_REVISION_ATTEMPTS} revision attempts. Routing to manual review."
            )
        elif final_status == "REVISION_REQUIRED":
            job.status = JobStatus.REVISION_REQUIRED
            job.current_step = "REVISION_REQUIRED"
            log_activity_sync(
                db, job_id, "REVISION_REQUIRED", "WARNING",
                "Quality audit requested draft revisions."
            )
        else:
            job.status = JobStatus.FAILED
            job.current_step = final_state.get("current_step", "FAILED")
            log_activity_sync(
                db, job_id, "WORKFLOW_FAILED", "FAILED",
                final_state.get("error_message") or "Workflow failed during processing."
            )

        db.commit()
        return {"job_id": job_id, "status": job.status.value}

    except Exception as e:
        db.rollback()
        job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.current_step = "ERROR"
            db.commit()
            log_activity_sync(db, job_id, "WORKFLOW_ERROR", "FAILED", f"Unhandled task error: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="tasks.publish_to_strapi")
def publish_to_strapi_task(job_id: str):
    db = SyncSessionLocal()
    job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
    if not job:
        db.close()
        return {"error": f"Job {job_id} not found."}

    # Verify state
    if job.status not in [JobStatus.APPROVED, JobStatus.PUBLISHING, JobStatus.FAILED]:
        db.close()
        return {"error": f"Job {job_id} must be APPROVED before publishing. Current status: {job.status}"}

    try:
        job.status = JobStatus.PUBLISHING
        job.current_step = "PUBLISHING"
        db.commit()
        log_activity_sync(db, job_id, "PUBLISH_START", "PROCESSING", "Sending article to Strapi CMS...")

        # Idempotency check: see if PublishingJob already exists with cms_entry_id
        existing_pub = db.query(PublishingJob).filter(PublishingJob.content_job_id == job_id).first()
        existing_cms_id = existing_pub.cms_entry_id if existing_pub else None
        existing_url = existing_pub.published_url if existing_pub else None

        final_md_content = MarkdownService.read_markdown(job_id, "05-final.md")
        if not final_md_content:
            final_md_content = job.topic # Fallback if file missing

        # Run Strapi publish async helper synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(
            StrapiService.publish_article(
                title=job.topic,
                content_body=final_md_content,
                category=job.category,
                existing_cms_id=existing_cms_id,
                existing_published_url=existing_url
            )
        )
        loop.close()

        if res["success"]:
            # Update PublishingJob record
            if not existing_pub:
                existing_pub = PublishingJob(content_job_id=job_id)
                db.add(existing_pub)

            existing_pub.cms = "strapi"
            existing_pub.cms_entry_id = res["cms_entry_id"]
            existing_pub.published_url = res["published_url"]
            existing_pub.status = "PUBLISHED"
            existing_pub.http_status = res["http_status"]
            existing_pub.published_at = datetime.utcnow()

            # Mark job as PUBLISHED
            job.status = JobStatus.PUBLISHED
            job.current_step = "PUBLISHED"
            db.commit()

            log_activity_sync(
                db, job_id, "PUBLISH_SUCCESS", "SUCCESS",
                f"Successfully published to Strapi. Entry ID: {res['cms_entry_id']}, URL: {res['published_url']}"
            )

            # ONLY NOW delete temporary markdown files!
            deleted = MarkdownService.delete_job_files(job_id)
            if deleted:
                log_activity_sync(db, job_id, "FILE_CLEANUP", "SUCCESS", "Temporary markdown files safely deleted.")
            
            return {"job_id": job_id, "status": "PUBLISHED", "url": res["published_url"]}
        else:
            # Publishing failed -> DO NOT DELETE FILES
            if not existing_pub:
                existing_pub = PublishingJob(content_job_id=job_id)
                db.add(existing_pub)

            existing_pub.status = "FAILED"
            existing_pub.error_message = res.get("error_message")
            existing_pub.http_status = res.get("http_status")
            existing_pub.retry_count = (existing_pub.retry_count or 0) + 1

            job.status = JobStatus.FAILED
            job.current_step = "PUBLISH_FAILED"
            db.commit()

            log_activity_sync(
                db, job_id, "PUBLISH_FAILED", "FAILED",
                f"Strapi publication failed: {res.get('error_message')}. Temporary files preserved for retry."
            )
            return {"job_id": job_id, "status": "FAILED", "error": res.get("error_message")}

    except Exception as e:
        db.rollback()
        job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.current_step = "PUBLISH_ERROR"
            db.commit()
            log_activity_sync(db, job_id, "PUBLISH_ERROR", "FAILED", f"Exception during publication: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="tasks.revise_content_job")
def revise_content_job_task(job_id: str):
    db = SyncSessionLocal()
    job = db.query(ContentJob).filter(ContentJob.id == job_id).first()
    if not job:
        db.close()
        return {"error": f"Job {job_id} not found."}

    try:
        job_data = {
            "topic": job.topic,
            "primary_keyword": job.primary_keyword,
            "search_volume": job.search_volume,
            "keyword_difficulty": job.keyword_difficulty,
            "target_density": job.target_density,
            "audience": job.audience
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        log_activity_sync(db, job_id, "REVISION_START", "STARTED", "Executing draft revision based on quality audit findings...")

        # Run RevisionAgent
        loop.run_until_complete(RevisionAgent.run(job_id, job_data))
        job.retry_count = (job.retry_count or 0) + 1
        job.status = JobStatus.QUALITY_CHECK
        job.current_step = "QUALITY_CHECK"
        db.commit()

        # Run QualityAgent evaluation after revision
        passed, result_status, metrics = loop.run_until_complete(
            QualityAgent.evaluate_and_finalize(job_id, job_data, force_finalize=False)
        )
        loop.close()

        if passed:
            job.status = JobStatus.AWAITING_APPROVAL
            job.current_step = "AWAITING_APPROVAL"
            
            final_article_text = MarkdownService.read_markdown(job_id, "05-final.md") or job.topic
            existing_art = db.query(Article).filter(Article.job_id == job_id).first()
            if not existing_art:
                art = Article(
                    job_id=job_id,
                    title=job.topic,
                    slug=StrapiService.generate_slug(job.topic),
                    current_version=job.current_version or 1,
                    status="AWAITING_APPROVAL"
                )
                db.add(art)
                db.flush()

                ver = ArticleVersion(
                    article_id=art.id,
                    version_number=job.current_version or 1,
                    content_body=final_article_text,
                    change_summary="Revised version passing quality checks."
                )
                db.add(ver)

            log_activity_sync(db, job_id, "REVISION_SUCCESS", "SUCCESS", "Revised draft passed quality checks. Job moved to Human Review.")
        else:
            if job.retry_count < settings.MAX_REVISION_ATTEMPTS:
                job.status = JobStatus.REVISION_REQUIRED
                job.current_step = "REVISION_REQUIRED"
                log_activity_sync(db, job_id, "REVISION_ATTEMPT", "WARNING", f"Revision attempt {job.retry_count} completed. Further revisions required.")
            else:
                job.status = JobStatus.MANUAL_REVIEW_REQUIRED
                job.current_step = "MANUAL_REVIEW_REQUIRED"
                log_activity_sync(db, job_id, "REVISION_EXHAUSTED", "FAILED", f"Max revision attempts ({settings.MAX_REVISION_ATTEMPTS}) reached. Routed to Manual Review.")

        db.commit()
        return {"job_id": job_id, "status": job.status.value}

    except Exception as e:
        db.rollback()
        log_activity_sync(db, job_id, "REVISION_ERROR", "FAILED", f"Error during revision execution: {str(e)}")
        return {"error": str(e)}
    finally:
        db.close()

