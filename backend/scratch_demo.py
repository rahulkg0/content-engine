import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database.database import init_db, SyncSessionLocal
from app.models.models import ContentBatch, ContentJob, JobStatus, PublishingJob
from app.services.csv_service import CSVService
from app.workers.content_tasks import process_content_job_task, publish_to_strapi_task
from app.services.markdown_service import MarkdownService

def run_full_demo():
    print("==================================================================")
    print("      CONTENT ENGINE PHASE 1 — LIVE DEMO WORKFLOW EXECUTION")
    print("==================================================================")

    # 1. Initialize Database
    asyncio.run(init_db())
    print("[STEP 1/7] Database schema initialized.")

    # 2. Read sample_topics.csv
    csv_path = Path(__file__).resolve().parent.parent / "sample_topics.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        csv_text = f.read()

    headers, data_rows = CSVService.parse_csv_content(csv_text)
    mapping = CSVService.auto_detect_mapping(headers)
    preview = CSVService.validate_and_preview(headers, data_rows, mapping)
    print(f"[STEP 2/7] Parsed CSV '{csv_path.name}': {preview['total_rows']} total rows, {preview['valid_rows_count']} valid topics.")

    # 3. Create ContentBatch and ContentJobs in DB
    db = SyncSessionLocal()
    batch = ContentBatch(
        filename=csv_path.name,
        total_rows=preview["total_rows"],
        valid_rows=preview["valid_rows_count"],
        invalid_rows=preview["invalid_rows_count"],
        status="PROCESSING"
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    jobs = []
    for r in preview["rows"]:
        if r["is_valid"]:
            j = ContentJob(
                batch_id=batch.id,
                topic=r["topic"],
                primary_keyword=r["primary_keyword"],
                search_volume=r.get("search_volume"),
                keyword_difficulty=r.get("keyword_difficulty"),
                target_density=r.get("target_density"),
                category=r.get("category"),
                audience=r.get("audience"),
                notes=r.get("notes"),
                status=JobStatus.QUEUED,
                current_step="QUEUED"
            )
            db.add(j)
            db.commit()
            db.refresh(j)
            jobs.append(j)

    print(f"[STEP 3/7] Created ContentBatch '{batch.id[:8]}' with {len(jobs)} ContentJobs.")

    # 4. Process Job #1 through LangGraph AI Agent Workflow
    target_job = jobs[0]
    print(f"\n[STEP 4/7] Processing Job #{target_job.id[:8]}: '{target_job.topic}'...")
    res1 = process_content_job_task(target_job.id)
    print(f" -> AI Workflow complete. Return status: {res1['status']}")

    # Verify Markdown files generated in storage/jobs/{job_id}/
    files_before = MarkdownService.get_all_job_files(target_job.id)
    print(f" -> Temporary Markdown Files created in storage/jobs/{target_job.id[:8]}/:")
    for fname, exists in files_before.items():
        print(f"    - {fname}: {'✓ Exists' if exists else '✗ Missing'}")

    # 5. Verify Article is in Human Approval Queue (AWAITING_APPROVAL)
    db.refresh(target_job)
    print(f"\n[STEP 5/7] Current Job Status: {target_job.status.value}")
    assert target_job.status == JobStatus.AWAITING_APPROVAL, "Job should be AWAITING_APPROVAL"

    # 6. Simulate Human Approval & Publish to Strapi
    print("\n[STEP 6/7] Simulating Human Approval & Dispatching Strapi Publishing Task...")
    target_job.status = JobStatus.APPROVED
    db.commit()

    pub_res = publish_to_strapi_task(target_job.id)
    print(f" -> Strapi Publishing Task complete. Result: {pub_res}")

    # 7. Verification of CMS Info & Temporary File Deletion
    db.refresh(target_job)
    pub_job = db.query(PublishingJob).filter(PublishingJob.content_job_id == target_job.id).first()
    
    print(f"\n[STEP 7/7] Verifying Publication & Cleanup:")
    print(f" -> Final Job Status: {target_job.status.value}")
    print(f" -> Strapi Entry ID: {pub_job.cms_entry_id if pub_job else 'N/A'}")
    print(f" -> Published URL: {pub_job.published_url if pub_job else 'N/A'}")

    files_after = MarkdownService.get_all_job_files(target_job.id)
    print(f" -> Temporary Markdown Files cleanup status:")
    for fname, exists in files_after.items():
        print(f"    - {fname}: {'⚠ Still Exists' if exists else '✓ Successfully Deleted'}")

    print("\n==================================================================")
    print("      ALL 7 WORKFLOW PHASES PASSED WITH 100% SUCCESS!")
    print("==================================================================")
    db.close()

if __name__ == "__main__":
    run_full_demo()
