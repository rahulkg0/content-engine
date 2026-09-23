import asyncio
import httpx
from typing import Dict, Any, Optional
from app.config import settings

class OpenRouterService:
    @staticmethod
    async def generate_completion(
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8000,
        web_search: bool = False
    ) -> Dict[str, Any]:
        """
        Sends a completion request to OpenRouter API with rate-limit retry and model fallbacks.
        """
        chosen_model = model or settings.DEFAULT_WRITER_MODEL
        
        # DEMO Mode or missing key fallback handler
        if settings.DEMO_MODE or not settings.OPENROUTER_API_KEY or settings.OPENROUTER_API_KEY.startswith("mock"):
            return {
                "text": f"[DEMO MODE Output for Model: {chosen_model}]\n\n" + prompt[:500],
                "model": chosen_model,
                "usage": {"prompt_tokens": 150, "completion_tokens": 350, "total_tokens": 500},
                "estimated_cost": 0.0005,
                "is_demo": True
            }

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://content-engine.local",
            "X-Title": "AI Content Automation System",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # List of candidate models to try in order (prioritizing DeepSeek V4 Flash free model)
        if web_search:
            fallback_models = [
                chosen_model,
                "deepseek/deepseek-chat",
                "meta-llama/llama-3.3-70b-instruct:free",
                "google/gemini-2.0-flash-lite-preview-02-05:free",
                "openrouter/auto"
            ]
        else:
            fallback_models = [
                chosen_model,
                "deepseek/deepseek-chat",
                "meta-llama/llama-3.3-70b-instruct:free",
                "google/gemini-2.0-flash-lite-preview-02-05:free",
                "openrouter/auto"
            ]
            
        candidate_models = list(dict.fromkeys(fallback_models))

        last_error = None
        await asyncio.sleep(1)

        async with httpx.AsyncClient(timeout=120.0) as client:
            for target_model in candidate_models:
                payload = {
                    "model": target_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

                if web_search:
                    payload["plugins"] = [{"id": "web"}]

                # Retry up to 2 times per model
                for attempt in range(2):
                    try:
                        response = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=payload
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            choice = data["choices"][0]
                            text = choice["message"]["content"]
                            usage = data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
                            tokens = usage.get("total_tokens", 0)
                            cost = (tokens / 1000.0) * 0.002

                            return {
                                "text": text,
                                "model": data.get("model", target_model),
                                "usage": usage,
                                "estimated_cost": cost,
                                "is_demo": False
                            }
                        elif response.status_code == 402:
                            # Payment required/Out of credits -> skip immediately to next model
                            last_error = f"OpenRouter HTTP 402 ({target_model} out of credits): {response.text[:120]}"
                            break
                        elif response.status_code == 429:
                            last_error = f"OpenRouter HTTP 429 ({target_model} rate limit): {response.text[:120]}"
                            if attempt < 1:
                                await asyncio.sleep(3)
                                continue
                            else:
                                break
                        else:
                            # Try without plugins if web_search plugins rejected by model
                            if web_search and "plugins" in payload:
                                del payload["plugins"]
                                retry_res = await client.post(
                                    "https://openrouter.ai/api/v1/chat/completions",
                                    headers=headers,
                                    json=payload
                                )
                                if retry_res.status_code == 200:
                                    data = retry_res.json()
                                    choice = data["choices"][0]
                                    text = choice["message"]["content"]
                                    usage = data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
                                    return {
                                        "text": text,
                                        "model": data.get("model", target_model),
                                        "usage": usage,
                                        "estimated_cost": (usage.get("total_tokens", 0) / 1000.0) * 0.002,
                                        "is_demo": False
                                    }
                            last_error = f"OpenRouter returned HTTP {response.status_code}: {response.text[:150]}"
                            break
                    except Exception as e:
                        last_error = str(e)
                        await asyncio.sleep(2)

        raise Exception(f"OpenRouter API call failed across candidate models. Last error: {last_error}")
