"""OpenAI provider client."""
from __future__ import annotations

import os
from typing import Any

from openai import AsyncOpenAI

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    def __init__(self, model: str):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        logger.info("Calling OpenAI with user prompt: %s", user_prompt)
        response: Any = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content.strip()
        logger.info("OpenAI returned SPARQL: %s", content)
        return content

