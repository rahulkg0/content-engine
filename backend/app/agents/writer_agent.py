from typing import Dict, Any
from app.services.openrouter_service import OpenRouterService
from app.services.markdown_service import MarkdownService
from app.config import settings

class WriterAgent:
    @staticmethod
    async def run(job_id: str, job_data: Dict[str, Any], revision_notes: str = None) -> str:
        topic = job_data["topic"]
        primary_kw = job_data["primary_keyword"]

        research_content = MarkdownService.read_markdown(job_id, "01-research.md") or ""
        brief_content = MarkdownService.read_markdown(job_id, "02-content-brief.md") or ""

        revision_context = ""
        if revision_notes:
            revision_context = f"\n\nCRITICAL REVISION NOTES TO ADDRESS:\n{revision_notes}\n"

        prompt = f"""
You are writing a full-length, authoritative, in-depth blog article based on exhaustive live research and an expert content brief.

Topic: {topic}
Primary Keyword: {primary_kw}
{revision_context}

FULL RESEARCH DOSSIER (01-RESEARCH.MD):
{research_content[:6000]}

EXHAUSTIVE CONTENT BRIEF (02-CONTENT-BRIEF.MD):
{brief_content[:4000]}

INSTRUCTIONS:
1. Write a complete, comprehensive, highly engaging article with H1 title, compelling introduction, deep H2 and H3 subheadings, real-world examples, verified statistics, and actionable concluding takeaways.
2. Ensure natural editorial voice, clear explanations, and seamless keyword integration matching target density.
3. Do NOT shorten or summarize sections. Synthesize all key facts, current 2025/2026 developments, and evidence provided in the research dossier.
4. Ensure proper heading hierarchy and accurate claims.
"""

        res = await OpenRouterService.generate_completion(
            prompt=prompt,
            system_prompt="You are a Master Principal Editorial Writer. Synthesize extensive research into comprehensive, authoritative, engaging long-form articles.",
            model=settings.DEFAULT_WRITER_MODEL,
            max_tokens=8000
        )

        content = res["text"]
        MarkdownService.save_markdown(job_id, "03-draft.md", content)
        return content
