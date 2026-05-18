from collections.abc import Iterable
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from app.core.config import settings
from app.core.logger import logger


class AnthropicClient:
    _anthropic_client: AsyncAnthropic

    def __init__(self, api_key: str, model: str, max_tokens: int) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

    async def setup(self) -> None:
        self._anthropic_client = AsyncAnthropic(api_key=self.api_key)

    async def create_message(self, messages: Iterable[MessageParam]) -> Any:
        logger.info("llm_request_started", model=self.model)
        message = await self._anthropic_client.messages.create(
            max_tokens=self.max_tokens,
            model=self.model,
            messages=messages
        )
        logger.info("llm_request_finished", model=self.model)
        return message


anthropic_client = AnthropicClient(
    api_key=settings.ANTHROPIC_API_KEY,
    model=settings.ANTHROPIC_MODEL,
    max_tokens=settings.MAX_TOKENS
)
