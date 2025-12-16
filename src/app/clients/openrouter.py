import httpx
from typing import Any, Dict, List
from app.core.config import settings
import asyncio

class OpenRouterRateLimitError(RuntimeError):
    pass

class OpenRouterClient:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")

    async def query_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",

            # Optional but recommended by OpenRouter for attribution/analytics.
            # Add these if you have them in settings:
            # "HTTP-Referer": settings.APP_URL,
            # "X-Title": "LLM Court",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            # If 429, handle before raise_for_status so we can read headers safely
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                msg = "OpenRouter rate-limited (429)."
                if retry_after:
                    msg += f" Retry-After: {retry_after}s."
                raise OpenRouterRateLimitError(msg)

            r.raise_for_status()
            data = r.json()
            model_message = data["choices"][0]["message"]
            return {
                "content": model_message.get("content"),
                "reasoning_details": model_message.get("reasoning"),
            }

        except httpx.HTTPStatusError as e:
            # Non-429 HTTP errors
            raise RuntimeError(
                f"OpenRouter API request failed: {e.response.status_code} {e.response.text}"
            ) from e
        except httpx.HTTPError as e:
            raise RuntimeError(f"OpenRouter network error: {e}") from e

        # for attempt in range(max_retries + 1):
        #     try:
        #         async with httpx.AsyncClient(timeout=60.0) as client:
        #             r = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)

        #         # If 429, handle before raise_for_status so we can read headers safely
        #             if r.status_code == 429:
        #                 retry_after = r.headers.get("Retry-After")
        #                 wait_s = float(retry_after) if retry_after and retry_after.isdigit() else (1.5 * (2 ** attempt))
        #                 if attempt < max_retries:
        #                     await asyncio.sleep(wait_s)
        #                     continue
        #                 raise OpenRouterRateLimitError(
        #                     f"OpenRouter rate-limited (429). Try again in ~{wait_s:.1f}s or reduce request frequency."
        #                 )

        #             r.raise_for_status()
        #             data = r.json()
        #             model_message = data["choices"][0]["message"]
        #             return {
        #                 "content": model_message.get("content"),
        #                 "reasoning_details": model_message.get("reasoning"),
        #             }

        #     except httpx.HTTPStatusError as e:
        #         # Non-429 HTTP errors
        #         raise RuntimeError(f"OpenRouter API request failed: {e.response.status_code} {e.response.text}") from e
        #     except httpx.HTTPError as e:
        #         raise RuntimeError(f"OpenRouter network error: {e}") from e
    
    async def query_model_parallel(
        self,
        models: List[str],
        message: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        tasks = [self.query_model(model=m, messages=message) for m in models]
        results = await asyncio.gather(*tasks)
        return {m: r for m, r in zip(models, results)}