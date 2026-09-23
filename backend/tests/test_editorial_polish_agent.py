import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.agents.editorial_polish_agent import EditorialPolishAgent
from app.agents.quality_agent import QualityAgent
from app.services.markdown_service import MarkdownService
from app.models.models import JobStatus

SAMPLE_ARTICLE = """# Career Options in 2026: A Complete Guide

Choosing the right career options requires evaluating your personal skills and market demand.

In today's rapidly changing world, furthermore, it is important to note that technology plays a crucial role.

## Key Statistics and Research

According to recent labor statistics, 78% of technology professionals reported higher job satisfaction in 2025.
For detailed analysis, refer to https://example.com/career-data or (Smith et al., 2025).

### 1. High-Income Career Options

- **Software Engineering**: Focus on scalable cloud architecture and AI integrations.
- **Data Science**: Analyze complex datasets to drive business strategy.

In conclusion, taking time to explore various career options will set you up for long-term success.
"""

POLISHED_ARTICLE = """# Career Options in 2026: A Complete Guide

Choosing the right career options requires evaluating your personal skills against market demand.

Technology plays a central role in modern career planning.

## Key Statistics and Research

According to recent labor statistics, 78% of technology professionals reported higher job satisfaction in 2025.
For detailed analysis, refer to https://example.com/career-data or (Smith et al., 2025).

### 1. High-Income Career Options

- **Software Engineering**: Focus on scalable cloud architecture and AI integrations.
- **Data Science**: Analyze complex datasets to drive business strategy.

Taking time to explore various career options will set you up for long-term success.
"""

@pytest.mark.asyncio
async def test_successful_polishing():
    topic = "Career Options in 2026"
    primary_kw = "career options"
    
    with patch("app.services.openrouter_service.OpenRouterService.generate_completion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = {"text": POLISHED_ARTICLE, "model": "mock-model"}
        with patch("app.config.settings.DEMO_MODE", False):
            with patch("app.config.settings.OPENROUTER_API_KEY", "sk-or-v1-validkey"):
                result = await EditorialPolishAgent.polish(
                    SAMPLE_ARTICLE,
                    topic=topic,
                    primary_keyword=primary_kw
                )
                assert result.strip() == POLISHED_ARTICLE.strip()
                assert "78%" in result
                assert "https://example.com/career-data" in result
                assert "(Smith et al., 2025)" in result
                assert primary_kw in result.lower()

@pytest.mark.asyncio
async def test_empty_llm_response_fallback():
    with patch("app.services.openrouter_service.OpenRouterService.generate_completion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = {"text": "", "model": "mock-model"}
        with patch("app.config.settings.DEMO_MODE", False):
            with patch("app.config.settings.OPENROUTER_API_KEY", "sk-or-v1-validkey"):
                result = await EditorialPolishAgent.polish(SAMPLE_ARTICLE)
                assert result.strip() == SAMPLE_ARTICLE.strip()

@pytest.mark.asyncio
async def test_llm_api_failure_fallback():
    with patch("app.services.openrouter_service.OpenRouterService.generate_completion", new_callable=AsyncMock) as mock_completion:
        mock_completion.side_effect = Exception("OpenRouter 500 Server Error")
        with patch("app.config.settings.DEMO_MODE", False):
            with patch("app.config.settings.OPENROUTER_API_KEY", "sk-or-v1-validkey"):
                result = await EditorialPolishAgent.polish(SAMPLE_ARTICLE)
                # Ensures pipeline preserves original article without raising an exception
                assert result.strip() == SAMPLE_ARTICLE.strip()

@pytest.mark.asyncio
async def test_invalid_response_meta_commentary_fallback():
    meta_response = "Here is the revised article you requested:\n\n# Career Options in 2026..."
    with patch("app.services.openrouter_service.OpenRouterService.generate_completion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = {"text": meta_response, "model": "mock-model"}
        with patch("app.config.settings.DEMO_MODE", False):
            with patch("app.config.settings.OPENROUTER_API_KEY", "sk-or-v1-validkey"):
                result = await EditorialPolishAgent.polish(SAMPLE_ARTICLE)
                assert result.strip() == SAMPLE_ARTICLE.strip()

@pytest.mark.asyncio
async def test_preservation_of_facts_citations_urls_keywords():
    topic = "Career Options in 2026"
    primary_kw = "career options"
    
    with patch("app.services.openrouter_service.OpenRouterService.generate_completion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = {"text": POLISHED_ARTICLE, "model": "mock-model"}
        with patch("app.config.settings.DEMO_MODE", False):
            with patch("app.config.settings.OPENROUTER_API_KEY", "sk-or-v1-validkey"):
                result = await EditorialPolishAgent.polish(
                    SAMPLE_ARTICLE,
                    topic=topic,
                    primary_keyword=primary_kw
                )
                assert "# Career Options in 2026" in result
                assert "## Key Statistics and Research" in result
                assert "### 1. High-Income Career Options" in result
                assert "78%" in result
                assert "https://example.com/career-data" in result
                assert "(Smith et al., 2025)" in result
                assert primary_kw in result.lower()

@pytest.mark.asyncio
async def test_quality_agent_integration_and_approval_flow():
    job_id = "test-polish-job-1"
    job_data = {
        "topic": "Career Options in 2026",
        "primary_keyword": "career options",
        "target_density": "0.7-0.9%"
    }

    MarkdownService.save_markdown(job_id, "03-draft.md", SAMPLE_ARTICLE)

    with patch("app.services.openrouter_service.OpenRouterService.generate_completion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = {"text": POLISHED_ARTICLE, "model": "mock-model"}
        with patch("app.config.settings.DEMO_MODE", False):
            with patch("app.config.settings.OPENROUTER_API_KEY", "sk-or-v1-validkey"):
                passed, status_str, metrics = await QualityAgent.evaluate_and_finalize(
                    job_id=job_id,
                    job_data=job_data,
                    force_finalize=True
                )
                assert passed is True
                assert status_str in ["PASS", "PASSED"]

    final_saved = MarkdownService.read_markdown(job_id, "05-final.md")
    assert final_saved.strip() == POLISHED_ARTICLE.strip()

    # Clean up
    MarkdownService.delete_job_files(job_id)
