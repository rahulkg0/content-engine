import random
import re
from typing import Optional
from app.services.openrouter_service import OpenRouterService
from app.config import settings

AI_VOCAB_REPLACEMENTS = {
    "utilize": ["use", "apply", "work with"],
    "facilitate": ["help", "support", "enable"],
    "comprehensive": ["full", "complete", "thorough"],
    "subsequently": ["then", "after that", "next"],
    "furthermore": ["also", "plus", "on top of that"],
    "demonstrate": ["show", "prove", "illustrate"],
    "implement": ["build", "set up", "put in place"],
    "leverage": ["use", "take advantage of", "tap into"],
    "optimize": ["improve", "fine-tune", "make better"],
    "paradigm": ["model", "approach", "framework"],
    "synergy": ["teamwork", "combined effect", "collaboration"],
    "methodology": ["method", "approach", "process"],
    "innovative": ["new", "creative", "fresh"],
    "streamline": ["simplify", "speed up", "smooth out"],
    "unprecedented": ["never seen before", "unheard of", "groundbreaking"],
    "transformative": ["game-changing", "revolutionary", "major"],
    "ecosystem": ["environment", "landscape", "space"],
    "scalable": ["flexible", "expandable", "growable"],
    "robust": ["strong", "solid", "reliable"],
    "cutting-edge": ["latest", "advanced", "modern"],
    "delve": ["dig into", "explore", "look at"],
    "intricate": ["complex", "detailed", "involved"],
    "pivotal": ["key", "crucial", "central"],
    "encompasses": ["includes", "covers", "spans"],
    "multifaceted": ["complex", "varied", "diverse"],
    "realm": ["area", "field", "world"],
    "commendable": ["impressive", "notable", "praiseworthy"],
    "meticulous": ["careful", "thorough", "precise"],
    "paramount": ["essential", "critical", "top priority"],
    "underscore": ["highlight", "stress", "emphasize"],
}

class HumanizerAgent:
    """
    Humanizes AI-generated text using the multi-stage methodology from lynote-ai/humanize-text:
    1. LLM High-Variance Rewrite (Temperature 1.3 + burstiness/perplexity disruption prompt).
    2. AI Vocabulary Post-Processing (Replacing 30+ canonical AI buzzwords).
    3. Sentence Rhythm Disruption (Combining short consecutive sentences to break robotic cadence).
    """

    @staticmethod
    def _replace_ai_vocabulary(text: str) -> str:
        for word, replacements in AI_VOCAB_REPLACEMENTS.items():
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            if pattern.search(text):
                replacement = random.choice(replacements)
                text = pattern.sub(replacement, text)
        return text

    @staticmethod
    def _disrupt_sentence_rhythm(text: str) -> str:
        paragraphs = text.split('\n\n')
        processed_paragraphs = []
        
        for para in paragraphs:
            # Preserve headings, code blocks, lists
            if para.strip().startswith(('#', '-', '*', '`', '1.', '2.', '3.')):
                processed_paragraphs.append(para)
                continue
                
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', para) if s.strip()]
            if len(sentences) < 3:
                processed_paragraphs.append(para)
                continue

            result = []
            i = 0
            while i < len(sentences):
                words_current = len(sentences[i].split())
                if (i + 1 < len(sentences)
                        and words_current < 8
                        and len(sentences[i + 1].split()) < 8):
                    merged = sentences[i].rstrip('.!?') + " — " + sentences[i + 1][0].lower() + sentences[i + 1][1:]
                    result.append(merged)
                    i += 2
                else:
                    result.append(sentences[i])
                    i += 1
            processed_paragraphs.append(" ".join(result))

        return '\n\n'.join(processed_paragraphs)

    @classmethod
    async def humanize(cls, article_text: str, topic: str, primary_keyword: str) -> str:
        if settings.DEMO_MODE or not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY.startswith("mock"):
            text = cls._replace_ai_vocabulary(article_text)
            return cls._disrupt_sentence_rhythm(text)

        prompt = f"""
You are an expert Human Content Editor specializing in converting AI-generated drafts into natural, highly engaging, authentic human-sounding articles.

Target Topic: {topic}
Primary Keyword to Preserve: {primary_keyword}

Below is the article draft to humanize:
--------------------------------------------------
{article_text}
--------------------------------------------------

HUMANIZATION INSTRUCTIONS (inspired by lynote-ai/humanize-text AI disruption techniques):
1. **Sentence Geometry & Burstiness**: Mix sentence lengths dramatically. Pair short 4-8 word punchy statements with longer 20-30 word detailed explanations. Break up monotonous AI sentence cadences.
2. **Eliminate AI Clichés & Buzzwords**: Remove robotic filler words like "Furthermore", "Moreover", "In conclusion", "In today's fast-paced digital world", "Tapestry", "Delve", "Testament", "Beacon", "Seamless", "Transformative", "Harness", "Spearhead", "Crucial role", "Paramount". Replace them with natural, direct transitions.
3. **Natural Conversational Voice**: Use clear active voice, natural contractions (don't, it's, we've, you'll), and engaging, relatable phrasing.
4. **Preserve Structure & Formatting**: Maintain all Markdown headings (H1, H2, H3), bullet points, bold tags, tables, and code snippets exactly.
5. **Preserve Factuality & Keyword**: Keep all facts, numbers, data points, and the primary keyword '{primary_keyword}' intact.

Return ONLY the complete humanized Markdown article text. Do not include meta-commentary, markdown backtick wrappers, or introductory chatter.
"""

        try:
            # Temperature 1.3 as recommended by lynote-ai/humanize-text for creative variance
            res = await OpenRouterService.generate_completion(
                prompt=prompt,
                system_prompt="You are a master editor who humanizes AI text into authentic, natural human prose.",
                model=settings.DEFAULT_WRITER_MODEL,
                temperature=1.3
            )
            humanized_text = res["text"].strip()
            if humanized_text.startswith("```markdown"):
                humanized_text = humanized_text[11:].strip()
            if humanized_text.startswith("```") and humanized_text.endswith("```"):
                humanized_text = humanized_text[3:-3].strip()

            if humanized_text and len(humanized_text) > 100:
                # Apply post-processing (AI vocab replacement + rhythm disruption)
                post_processed = cls._replace_ai_vocabulary(humanized_text)
                return cls._disrupt_sentence_rhythm(post_processed)
            
            # Fallback to original with post-processing
            post_processed = cls._replace_ai_vocabulary(article_text)
            return cls._disrupt_sentence_rhythm(post_processed)

        except Exception as e:
            print(f"Humanizer fallback warning: {e}")
            post_processed = cls._replace_ai_vocabulary(article_text)
            return cls._disrupt_sentence_rhythm(post_processed)

