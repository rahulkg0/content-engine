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
        from app.agents.editorial_polish_agent import EditorialPolishAgent
        return await EditorialPolishAgent.polish(
            article_text,
            topic=topic,
            primary_keyword=primary_keyword
        )


