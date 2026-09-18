from typing import Dict, Any
from app.services.research_service import ResearchService
from app.services.openrouter_service import OpenRouterService
from app.services.markdown_service import MarkdownService
from app.config import settings

class ResearchAgent:
    @staticmethod
    async def run(job_id: str, job_data: Dict[str, Any]) -> str:
        topic = job_data["topic"]
        primary_kw = job_data["primary_keyword"]
        vol = job_data.get("search_volume")
        kd = job_data.get("keyword_difficulty")
        density = job_data.get("target_density")
        audience = job_data.get("audience")

        if not settings.DEMO_MODE and settings.OPENROUTER_API_KEY and not settings.OPENROUTER_API_KEY.startswith("mock"):
            prompt = f"""
Conduct FULL, DEEP-DIVE, EXHAUSTIVE LIVE WEB RESEARCH for the following topic using your live web search capabilities.

Topic: {topic}
Primary Keyword: {primary_kw}
Search Volume: {vol or 'N/A'}
KD: {kd or 'N/A'}
Target Density: {density or '0.8-1.0%'}
Target Audience: {audience or 'General Professionals'}

IMPORTANT INSTRUCTIONS FOR FULL RESEARCH:
1. Do NOT write a brief summary or concise outline. Provide a FULL, DEEP-DIVE RESEARCH DOSSIER containing complete paragraphs, thorough explanations, data points, and context.
2. Perform live web searches to find up-to-date 2025/2026 facts, current industry developments, real statistics, and recent official/academic sources.
3. Prioritize: 1. Official sources 2. Government sources 3. Academic sources 4. Primary company sources 5. Reputable industry publications.
4. Never fabricate URLs, statistics, quotes, or facts. If evidence cannot be found, mark EVIDENCE_NOT_FOUND.

Format output adhering strictly to the Markdown schema below:

# Research
## Topic
{topic}
## Primary Keyword
{primary_kw}
## Search Volume
{vol or 'N/A'}
## Keyword Difficulty
{kd or 'N/A'}
## Target Density
{density or '0.8-1.0%'}
## Search Intent
[In-depth multi-paragraph analysis of user search intent, informational vs transactional needs, and core user goals]

## Target Audience
[Detailed demographic, professional, and behavioral breakdown of the target audience]

## Research Summary
[Extensive 4-5 paragraph deep-dive research overview explaining the current landscape, historical evolution, key drivers, and core concepts around the topic]

## Key Facts
- [Fact 1: Full detailed paragraph with context and implications]
- [Fact 2: Full detailed paragraph with context and implications]
- [Fact 3: Full detailed paragraph with context and implications]
- [Fact 4: Full detailed paragraph with context and implications]
- [Fact 5: Full detailed paragraph with context and implications]

## Statistics
- [Stat 1: Exact metric, percentage, sample size, year (2024-2026), and conducting institution]
- [Stat 2: Exact metric, percentage, sample size, year (2024-2026), and conducting institution]
- [Stat 3: Exact metric, percentage, sample size, year (2024-2026), and conducting institution]
- [Stat 4: Exact metric, percentage, sample size, year (2024-2026), and conducting institution]

## Current Developments
- [Development 1: Detailed analysis of 2025/2026 industry shifts or technological advancements]
- [Development 2: Detailed analysis of 2025/2026 industry shifts or technological advancements]
- [Development 3: Detailed analysis of 2025/2026 industry shifts or technological advancements]

## Content Gaps
- [Gap 1: Detailed description of what competitor articles omit and how to outperform existing content]
- [Gap 2: Detailed description of what competitor articles omit and how to outperform existing content]
- [Gap 3: Detailed description of what competitor articles omit and how to outperform existing content]

## Reader Questions
- [Question 1: Full comprehensive multi-paragraph answer]
- [Question 2: Full comprehensive multi-paragraph answer]
- [Question 3: Full comprehensive multi-paragraph answer]

## Claims and Evidence
### Claim 1
Claim: [Specific factual claim]
Evidence: [Detailed supporting evidence, study parameters, or official documentation]
Source: [Official source title and organization]
Confidence: HIGH / MEDIUM / LOW

### Claim 2
Claim: [Specific factual claim]
Evidence: [Detailed supporting evidence, study parameters, or official documentation]
Source: [Official source title and organization]
Confidence: HIGH / MEDIUM / LOW

### Claim 3
Claim: [Specific factual claim]
Evidence: [Detailed supporting evidence, study parameters, or official documentation]
Source: [Official source title and organization]
Confidence: HIGH / MEDIUM / LOW

## Sources
1. [Official Source Title]
   URL: [Exact live Web URL found]
   Source type: Government / Academic / Official / Industry
   Publication date: [Year/Date]
2. [Official Source Title]
   URL: [Exact live Web URL found]
   Source type: Government / Academic / Official / Industry
   Publication date: [Year/Date]
3. [Official Source Title]
   URL: [Exact live Web URL found]
   Source type: Government / Academic / Official / Industry
   Publication date: [Year/Date]

## Research Warnings
[Any research warnings or note of missing data]
"""
            llm_res = await OpenRouterService.generate_completion(
                prompt=prompt,
                system_prompt="You are a Senior Principal Research Director conducting live web research. Produce exhaustive, deep-dive research dossiers with real URLs and latest 2025/2026 data.",
                model=settings.DEFAULT_RESEARCH_MODEL,
                web_search=True,
                max_tokens=8000
            )
            content = llm_res["text"]
        else:
            research_res = await ResearchService.perform_research(
                topic=topic,
                primary_keyword=primary_kw,
                search_volume=vol,
                keyword_difficulty=kd,
                target_density=density,
                target_audience=audience
            )

            md = []
            md.append("# Research")
            md.append(f"## Topic\n{research_res['topic']}")
            md.append(f"## Primary Keyword\n{research_res['primary_keyword']}")
            md.append(f"## Search Volume\n{research_res['search_volume']}")
            md.append(f"## Keyword Difficulty\n{research_res['keyword_difficulty']}")
            md.append(f"## Target Density\n{research_res['target_density']}")
            md.append(f"## Search Intent\n{research_res['search_intent']}")
            md.append(f"## Target Audience\n{research_res['target_audience']}")
            md.append(f"## Research Summary\n{research_res['research_summary']}")
            
            md.append("## Key Facts")
            for fact in research_res["key_facts"]:
                md.append(f"- {fact}")
                
            md.append("\n## Statistics")
            for stat in research_res["statistics"]:
                md.append(f"- {stat}")
                
            md.append("\n## Current Developments")
            for dev in research_res["current_developments"]:
                md.append(f"- {dev}")
                
            md.append("\n## Content Gaps")
            for gap in research_res["content_gaps"]:
                md.append(f"- {gap}")
                
            md.append("\n## Reader Questions")
            for q in research_res["reader_questions"]:
                md.append(f"- {q}")
                
            md.append("\n## Claims and Evidence")
            for i, claim in enumerate(research_res["claims"], start=1):
                md.append(f"### Claim {i}")
                md.append(f"Claim:\n{claim['claim']}")
                md.append(f"Evidence:\n{claim['evidence']}")
                md.append(f"Source:\n{claim['source']}")
                md.append(f"Confidence:\n{claim['confidence']}\n")
                
            md.append("## Sources")
            for i, src in enumerate(research_res["sources"], start=1):
                md.append(f"{i}. {src['title']}")
                md.append(f"   URL: {src['url']}")
                md.append(f"   Source type: {src['source_type']}")
                md.append(f"   Publication date: {src['publication_date']}")
                
            md.append(f"\n## Research Warnings\n{research_res['warnings']}")
            content = "\n".join(md)

        MarkdownService.save_markdown(job_id, "01-research.md", content)
        return content
