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

    @property
    def client(self) -> AsyncAnthropic:
        if not hasattr(self, "_anthropic_client"):
            raise RuntimeError("Anthropic client is not initialized")
        return self._anthropic_client

    async def setup(self) -> None:
        self._anthropic_client = AsyncAnthropic(api_key=self.api_key)

    async def create_message(self, messages: Iterable[MessageParam], **kwargs: Any) -> Any:
        logger.info("llm_request_started", model=self.model)
        try:
            message = await self.client.messages.create(
                max_tokens=self.max_tokens,
                model=self.model,
                messages=messages,
                **kwargs
            )
        except Exception:
            logger.exception("llm_request_failed", model=self.model)
            raise
        logger.info("llm_request_finished", model=self.model)
        return message

    def stream_message(self, messages: Iterable[MessageParam], **kwargs: Any) -> Any:
        logger.info("llm_stream_started", model=self.model)
        return self.client.messages.stream(
            max_tokens=self.max_tokens,
            model=self.model,
            messages=messages,
            **kwargs
        )


anthropic_client = AnthropicClient(
    api_key=settings.ANTHROPIC_API_KEY,
    model=settings.ANTHROPIC_MODEL,
    max_tokens=settings.MAX_TOKENS
)
