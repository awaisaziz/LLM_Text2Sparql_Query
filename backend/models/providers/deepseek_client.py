"""DeepSeek provider client using OpenAI-compatible API."""
from __future__ import annotations

import os
from typing import Any

from openai import AsyncOpenAI

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DeepSeekClient:
    def __init__(self, model: str):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not set in environment variables")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        logger.info("Calling DeepSeek with user prompt: %s", user_prompt)
        response: Any = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content.strip()
        logger.info("DeepSeek returned SPARQL: %s", content)
        return content

