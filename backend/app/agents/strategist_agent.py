from typing import Dict, Any
from app.services.openrouter_service import OpenRouterService
from app.services.markdown_service import MarkdownService
from app.config import settings

class StrategistAgent:
    @staticmethod
    async def run(job_id: str, job_data: Dict[str, Any]) -> str:
        topic = job_data["topic"]
        primary_kw = job_data["primary_keyword"]
        research_content = MarkdownService.read_markdown(job_id, "01-research.md") or ""

        prompt = f"""
Conduct live web analysis on top-ranking SERP competitors and construct an EXHAUSTIVE, HIGHLY DETAILED CONTENT BRIEF.

Topic: {topic}
Primary Keyword: {primary_kw}

Comprehensive 01-Research Dossier:
{research_content[:4000]}

Perform live web search to analyze current ranking competitor headlines, popular subtopics, featured snippets, and user expectations.

Generate a comprehensive brief formatted as Markdown:
# Content Brief
## Recommended Title
[SEO-optimized title tag with primary keyword]

## Search Intent
[Detailed breakdown of search intent and content positioning]

## Target Audience
[Audience persona, skill level, and core questions]

## Article Objective
[Primary educational and conversion goals]

## Unique Angle
[Specific value proposition and unique angle that outperforms existing top 10 search results]

## Primary & Secondary Keywords
- Primary Keyword: {primary_kw}
- Secondary Keywords: [List 5-8 relevant LSI and long-tail keywords with search intent]

## Outline Structure
### H1: Main Article Title
### H2: Section 1 Title
- Core message and key data points to cover
- Subsections (H3s)
### H2: Section 2 Title
- Core message and key data points to cover
- Subsections (H3s)
### H2: Section 3 Title
- Core message and key data points to cover
- Subsections (H3s)
### H2: Section 4 Title
- Core message and key data points to cover
- Subsections (H3s)
### H2: Conclusion & Key Takeaways

## Questions to Answer
- [Question 1]
- [Question 2]
- [Question 3]

## Facts and Data Points to Include
- [Fact 1]
- [Fact 2]

## Recommended Internal Links
- [Internal topic cluster link 1]
- [Internal topic cluster link 2]

## Recommended External Sources
- [Official authority source 1 with live URL]
- [Official authority source 2 with live URL]

## Suggested Call to Action (CTA)
[Actionable next step for the reader]
"""

        res = await OpenRouterService.generate_completion(
            prompt=prompt,
            system_prompt="You are a Lead SEO Content Strategist. Create comprehensive, competitive content briefs backed by live web search.",
            model=settings.DEFAULT_RESEARCH_MODEL,
            web_search=True,
            max_tokens=6000
        )

        content = res["text"]
        if not content.startswith("# Content Brief"):
            content = f"# Content Brief: {topic}\n\n" + content

        MarkdownService.save_markdown(job_id, "02-content-brief.md", content)
        return content
