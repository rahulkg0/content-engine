import re
from typing import Optional
from app.services.openrouter_service import OpenRouterService
from app.config import settings

EDITORIAL_POLISH_PROMPT = """You are an expert human editor and experienced content writer.

Your task is to polish the provided article so that it reads naturally, clearly, professionally, and engagingly for real human readers.

This is an editorial-quality task.

Do not rewrite the article from scratch.

Preserve the original meaning, factual information, structure, evidence, citations, URLs, statistics, and SEO intent.

Your goal is to improve the reading experience, not to change the information.

NATURAL WRITING

Improve:
- Natural sentence flow
- Sentence variety
- Paragraph flow
- Clarity
- Readability
- Word choice
- Natural transitions
- Repetitive wording
- Awkward phrasing
- Generic filler
- Overly mechanical language
- Unnecessary formality
- Repetitive sentence structures

Make the writing feel like it has been carefully edited by an experienced human editor.

Do not make every sentence the same length.
Use a natural mixture of short, medium, and longer sentences.
Allow paragraphs to have different lengths when appropriate.
Do not make the writing artificially casual.
Keep the tone appropriate for the target audience and subject.

REMOVE GENERIC FILLER

Avoid unnecessary phrases such as:
- "In today's rapidly changing world"
- "In the modern era"
- "It is important to note"
- "Moreover"
- "Furthermore"
- "In conclusion"
- "As we all know"
- "Whether you are..."
- "Not only... but also..."

Do not mechanically replace these phrases.
Only remove them when they are unnecessary or make the writing feel repetitive.

INTRODUCTION

Improve the introduction so it gets to the reader's actual question, problem, or topic quickly.
Avoid generic introductions that could be used for hundreds of unrelated articles.
Do not add new facts simply to make the introduction more interesting.

BODY

For each section:
- Get to the point.
- Explain ideas clearly.
- Improve transitions where necessary.
- Remove repetition.
- Improve paragraph flow.
- Make explanations more concrete when the existing content supports it.
- Keep useful examples.
- Do not add unsupported examples.
- Do not unnecessarily convert paragraphs into bullet lists.
- Do not unnecessarily remove useful bullet lists.

CONCLUSION

Make the conclusion concise and useful.
Do not simply repeat the introduction.
Do not add generic motivational statements.

SEO

Preserve the primary keyword.
Use the primary keyword naturally.

Do NOT:
- Add keyword stuffing
- Force exact-match keywords
- Insert keywords into awkward sentences
- Repeat the keyword simply to increase density
- Sacrifice readability for keyword density

If existing keyword placement is already natural, leave it alone.

FACTUAL INTEGRITY

This is critical.

DO NOT:
- Invent facts
- Invent statistics
- Invent studies
- Invent research
- Invent citations
- Invent URLs
- Invent expert quotes
- Invent personal experiences
- Invent company information
- Invent dates
- Invent sources

DO NOT change:
- Numbers
- Statistics
- Dates
- Names
- URLs
- Citations
- Source references
- Factual claims

If a sentence sounds awkward but contains an important factual claim, improve only its wording while preserving the factual meaning.

PERSONAL EXPERIENCE

Do not create fake first-person experiences.

Do not write:
"I have seen this myself..."
"In my experience..."
"When I worked with..."
"I remember..."
unless such information already exists in the supplied article.

The article should feel natural without pretending to have personal experience.

STRUCTURE

Preserve the existing:
- H1
- H2
- H3
- Tables
- Lists
- Links
- Citations
- Markdown formatting

Do not restructure the article unnecessarily.
Do not add unnecessary headings.
Do not remove useful headings.

DO NOT OPTIMIZE FOR AI DETECTORS

Do not deliberately manipulate the text to bypass AI detection systems.
Do not deliberately introduce mistakes.
Do not intentionally make the writing worse.

Focus entirely on genuine editorial quality and reader experience.

FINAL CHECK

Before returning the article, silently check:
- Is the writing natural?
- Is the sentence structure varied?
- Is the article repetitive?
- Is there unnecessary filler?
- Are transitions natural?
- Are paragraphs easy to read?
- Is the tone appropriate?
- Is the keyword usage natural?
- Did I preserve every important fact?
- Did I preserve statistics?
- Did I preserve citations?
- Did I preserve URLs?
- Did I accidentally introduce a new factual claim?
- Did I change the meaning?

Fix any problems before returning the result.

OUTPUT

Return ONLY the polished article in Markdown.

Do not return:
- Analysis
- Explanation
- Editorial notes
- Comments
- Quality scores
- Revision notes
- "Here is the revised article"
- AI-related commentary

Start directly with the article.
"""

META_COMMENTARY_PATTERNS = [
    r"^here\s+is\s+(the|your)\s+(revised|polished|edited|article)",
    r"^i\s+have\s+(polished|edited|revised|improved)",
    r"^as\s+an\s+ai",
    r"^below\s+is\s+the\s+(polished|edited|revised)",
    r"^certainly,?\s+here",
    r"^sure,?\s+here"
]

class EditorialPolishAgent:
    """
    Editorial Polish Agent: Performs a final editorial polish on the generated article
    to improve naturalness, sentence flow, transitions, and clarity while strictly
    preserving factual accuracy, numbers, statistics, citations, URLs, search intent,
    and markdown structure.
    """

    @classmethod
    def _is_valid_polished_response(cls, original_text: str, polished_text: str) -> bool:
        if not polished_text or not isinstance(polished_text, str):
            return False
        
        polished_clean = polished_text.strip()
        if len(polished_clean) < 100:
            return False
        
        # Check minimum relative length to prevent massive truncation
        if len(original_text) > 300 and len(polished_clean) < len(original_text) * 0.35:
            return False

        # Check for meta-commentary in the first line
        first_line = polished_clean.split('\n')[0].strip().lower()
        for pattern in META_COMMENTARY_PATTERNS:
            if re.search(pattern, first_line):
                return False

        return True

    @classmethod
    async def polish(
        cls,
        article_text: str,
        topic: Optional[str] = None,
        primary_keyword: Optional[str] = None,
        audience: Optional[str] = None
    ) -> str:
        """
        Polishes final article text.
        Returns polished Markdown text if successful and validated.
        Returns original article_text if LLM call fails, times out, or fails validation.
        """
        if not article_text or not article_text.strip():
            return article_text

        # In DEMO_MODE or missing API key, return original or basic demo polish
        if settings.DEMO_MODE or not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY.startswith("mock"):
            return article_text

        context_header = ""
        if topic or primary_keyword or audience:
            context_header = f"Target Topic: {topic or 'N/A'}\nPrimary Keyword: {primary_keyword or 'N/A'}\nTarget Audience: {audience or 'N/A'}\n\n"

        prompt = f"""{context_header}--- ARTICLE TO POLISH ---
{article_text}
--- END ARTICLE ---
"""

        try:
            res = await OpenRouterService.generate_completion(
                prompt=prompt,
                system_prompt=EDITORIAL_POLISH_PROMPT,
                model=settings.DEFAULT_WRITER_MODEL,
                temperature=0.5
            )
            
            polished_text = res.get("text", "").strip()
            
            # Strip markdown code block wrappers if model enclosed entire response in ```markdown ... ```
            if polished_text.startswith("```markdown"):
                polished_text = polished_text[11:].strip()
            elif polished_text.startswith("```md"):
                polished_text = polished_text[5:].strip()
            if polished_text.startswith("```") and polished_text.endswith("```"):
                polished_text = polished_text[3:-3].strip()

            if cls._is_valid_polished_response(article_text, polished_text):
                return polished_text
            else:
                print(f"EditorialPolishAgent warning: Validation failed for LLM response. Falling back to original article.")
                return article_text

        except Exception as e:
            print(f"EditorialPolishAgent error: LLM completion failed ({e}). Preserving original article.")
            return article_text
