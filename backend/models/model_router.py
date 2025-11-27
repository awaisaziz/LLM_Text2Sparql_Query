"""Model router to abstract provider-specific clients."""
from __future__ import annotations

import asyncio
from typing import Dict, Type

from backend.models.providers.deepseek_client import DeepSeekClient
from backend.models.providers.gemini_client import GeminiClient
from backend.models.providers.openai_client import OpenAIClient
from backend.models.providers.openrouter_client import OpenRouterClient
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ModelRouter:
    def __init__(self, provider: str, model: str):
        providers: Dict[str, Type] = {
            "openai": OpenAIClient,
            "deepseek": DeepSeekClient,
            "gemini": GeminiClient,
            "openrouter": OpenRouterClient,
        }

        provider = provider.lower()
        if provider not in providers:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info("Initializing model router with provider=%s, model=%s", provider, model)
        self.client = providers[provider](model=model)

    async def generate(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        return await self.client.generate(system_prompt, user_prompt, max_tokens)

    def generate_sync(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """Synchronous wrapper around the async client for sequential batch runs."""

        return asyncio.run(self.generate(system_prompt, user_prompt, max_tokens))

