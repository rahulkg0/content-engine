import re
from typing import Dict, Any, Optional
from app.services.openrouter_service import OpenRouterService
from app.services.markdown_service import MarkdownService
from app.config import settings

class RevisionAgent:
    @staticmethod
    async def run(job_id: str, job_data: Dict[str, Any], version: int = 2) -> str:
        """
        Revises the article draft to fix specific issues identified in 04-quality-seo.md.
        Preserves passing sections and evidence, natural tone, and saves 03-draft-v{version}.md.
        """
        topic = job_data["topic"]
        primary_kw = job_data["primary_keyword"]
        target_density = job_data.get("target_density", "0.7-0.9%")
        audience = job_data.get("audience", "Target Audience")

        research = MarkdownService.read_markdown(job_id, "01-research.md") or ""
        brief = MarkdownService.read_markdown(job_id, "02-content-brief.md") or ""
        current_draft = MarkdownService.read_markdown(job_id, "03-draft.md") or ""
        quality_report = MarkdownService.read_markdown(job_id, "04-quality-seo.md") or ""

        if not settings.DEMO_MODE and settings.OPENROUTER_API_KEY and not settings.OPENROUTER_API_KEY.startswith("mock"):
            prompt = f"""
You are an expert AI Article Revision Editor. Your task is to revise and improve the existing article draft based strictly on Quality Audit feedback.

STRICT REVISION RULES:
1. Do NOT blindly rewrite the entire article. Preserve all sections, headings, and paragraphs that already passed audit.
2. Fix specific issues flagged in 04-QUALITY-SEO.MD (e.g. low keyword density or unsupported claims).
3. Primary Keyword: "{primary_kw}". Target Density: {target_density}. Ensure natural, conversational placement without keyword stuffing.
4. Never fabricate facts, statistics, citations, URLs, or quotes. Use available research context only. If an unsupported claim cannot be verified, remove or rewrite it safely.
5. Preserve search intent and audience alignment for {audience}.
6. Output ONLY the complete revised markdown article. Do NOT include editorial meta-commentary.

--- TOPIC & METADATA ---
Topic: {topic}
Primary Keyword: {primary_kw}
Target Density: {target_density}
Target Audience: {audience}

--- 01-RESEARCH.MD CONTEXT ---
{research[:2000]}

--- 02-CONTENT-BRIEF.MD CONTEXT ---
{brief[:1500]}

--- 04-QUALITY-SEO.MD AUDIT FINDINGS ---
{quality_report[:2000]}

--- CURRENT DRAFT (TO REVISE) ---
{current_draft[:4000]}
"""
            llm_res = await OpenRouterService.generate_completion(
                prompt=prompt,
                system_prompt="You are a professional Content Revision Editor. Fix identified quality/SEO issues while preserving high quality sections.",
                model=settings.DEFAULT_WRITER_MODEL
            )
            revised_draft = llm_res["text"]
        else:
            # DEMO mode revision logic: inject keyword naturally if density is low
            kw_count = len(re.findall(re.escape(primary_kw), current_draft, re.IGNORECASE))
            word_count = len(current_draft.split())
            density_pct = (kw_count / max(word_count, 1)) * 100

            revised_draft = current_draft
            if density_pct < 0.6:
                # Add natural occurrences of primary keyword
                insertion = f"\n\nFinding the right **{primary_kw}** requires aligning your core skills with market demand in 2026. Evaluating **{primary_kw}** effectively ensures long-term career growth.\n\n"
                if "##" in revised_draft:
                    parts = revised_draft.split("##", 1)
                    revised_draft = parts[0] + f"## {primary_kw.title()} Overview\n" + insertion + "##" + parts[1]
                else:
                    revised_draft = revised_draft + insertion

        # Save both versioned file (03-draft-v2.md) and active 03-draft.md
        MarkdownService.save_markdown_version(job_id, "03-draft.md", revised_draft, version=version)
        return revised_draft
