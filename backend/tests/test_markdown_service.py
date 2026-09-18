import os
import pytest
from app.services.markdown_service import MarkdownService

def test_markdown_lifecycle(tmp_path):
    job_id = "test_job_123"
    
    # Save files
    f1 = MarkdownService.save_markdown(job_id, "01-research.md", "# Research Data")
    f2 = MarkdownService.save_markdown(job_id, "05-final.md", "# Final Article")

    assert f1.exists()
    assert f2.exists()

    content = MarkdownService.read_markdown(job_id, "01-research.md")
    assert "# Research Data" in content

    status = MarkdownService.get_all_job_files(job_id)
    assert status["01-research.md"] is True
    assert status["05-final.md"] is True
    assert status["03-draft.md"] is False

    # Cleanup
    deleted = MarkdownService.delete_job_files(job_id)
    assert deleted is True
    assert not f1.exists()
