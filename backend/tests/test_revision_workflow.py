import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.agents.revision_agent import RevisionAgent
from app.agents.quality_agent import QualityAgent
from app.services.markdown_service import MarkdownService
from app.models.models import JobStatus

@pytest.mark.asyncio
async def test_revision_agent_creates_versioned_files():
    job_id = "test-revision-123"
    job_data = {
        "topic": "AI Content Automation",
        "primary_keyword": "AI content",
        "target_density": 2.5,
        "audience": "Marketers"
    }

    # Setup initial draft and quality audit files
    MarkdownService.save_markdown(job_id, "01-research.md", "# Research\nKey findings on AI content.")
    MarkdownService.save_markdown(job_id, "02-content-brief.md", "# Brief\nOutline and target keyword AI content.")
    MarkdownService.save_markdown(job_id, "03-draft.md", "# AI Content\nInitial draft content without high density.")
    MarkdownService.save_markdown(job_id, "04-quality-seo.md", "# Audit\nLow density flagged.")

    # Mock OpenRouter completion for RevisionAgent
    revised_text = "# AI Content (Revised)\nRevised draft content rich with AI content keyword."
    with patch("app.services.openrouter_service.OpenRouterService.generate_completion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = {"text": revised_text, "model": "mock-model"}
        with patch("app.config.settings.DEMO_MODE", False):
            with patch("app.config.settings.OPENROUTER_API_KEY", "sk-or-v1-testkey"):
                saved_text = await RevisionAgent.run(job_id, job_data, version=2)
                assert saved_text == revised_text

    # Check version 2 files created
    draft_v2 = MarkdownService.read_markdown(job_id, "03-draft-v2.md")
    draft_current = MarkdownService.read_markdown(job_id, "03-draft.md")
    assert draft_v2 == revised_text
    assert draft_current == revised_text

    # Cleanup
    MarkdownService.delete_job_files(job_id)


@pytest.mark.asyncio
async def test_quality_agent_evaluates_and_versions():
    job_id = "test-quality-123"
    job_data = {
        "topic": "SEO Optimization Guide",
        "primary_keyword": "SEO optimization",
        "target_density": 2.0
    }

    MarkdownService.save_markdown(job_id, "03-draft.md", "# SEO Optimization Guide\nDetailed guide to SEO optimization for website traffic.")

    json_response = '''```json
    {
        "passed": true,
        "scores": {"overall": 92, "seo": 95, "fact_check": 90, "editorial": 90},
        "seo": {"density": 2.1, "target": 2.0, "status": "PASS"},
        "fact_check": {"unsupported_claims": 0, "status": "PASS"},
        "editorial": {"score": 90, "status": "PASS"},
        "issues": []
    }
    ```'''

    with patch("app.services.openrouter_service.OpenRouterService.generate_completion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = {"text": json_response, "model": "mock-model"}
        with patch("app.config.settings.DEMO_MODE", False):
            with patch("app.config.settings.OPENROUTER_API_KEY", "sk-or-v1-testkey"):
                passed, status_str, metrics = await QualityAgent.evaluate_and_finalize(job_id, job_data, force_finalize=False)
                assert passed is True
                assert status_str in ["PASS", "PASSED"]

    final_art = MarkdownService.read_markdown(job_id, "05-final.md")
    assert final_art is not None

    # Cleanup
    MarkdownService.delete_job_files(job_id)


    # Cleanup


