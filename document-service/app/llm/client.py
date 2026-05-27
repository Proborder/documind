import asyncio
import random
from collections.abc import Iterable
from typing import Any

from anthropic import APIConnectionError, APIStatusError, AsyncAnthropic, RateLimitError
from anthropic.types import MessageParam

from app.core.config import settings
from app.core.exceptions import LLMUnavailableError
from app.core.logger import logger


class LLMClient:
    _anthropic_client: AsyncAnthropic

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int,
        max_attempts: int = 3,
        base_delay: float = 1.0
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.max_attempts = max_attempts
        self.base_delay = base_delay

    @property
    def client(self) -> AsyncAnthropic:
        if not hasattr(self, "_anthropic_client"):
            raise RuntimeError("Anthropic client is not initialized")
        return self._anthropic_client

    async def setup(self) -> None:
        self._anthropic_client = AsyncAnthropic(api_key=self.api_key)

    async def create_message(self, messages: Iterable[MessageParam], **kwargs: Any) -> Any:
        logger.info("llm_request_started", model=self.model)

        for attempt in range(1, self.max_attempts + 1):
            logger.info(
                "llm_request_attempt",
                attempt_number=attempt,
                error_type=None,
                wait_seconds=0
            )
            try:
                message = await self.client.messages.create(
                    max_tokens=self.max_tokens,
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
                logger.info("llm_request_finished", model=self.model)
                return message
            except (RateLimitError, APIConnectionError) as ex:
                if attempt == self.max_attempts:
                    logger.warning(
                        "llm_retry_exhausted",
                        attempt_number=attempt,
                        error=str(ex),
                        wait_seconds=0
                    )
                    raise LLMUnavailableError from ex

                wait_seconds = self._retry_delay(attempt, ex)
                logger.warning(
                    "llm_retry_scheduled",
                    attempt_number=attempt,
                    error=str(ex),
                    wait_seconds=wait_seconds
                )
                await asyncio.sleep(wait_seconds)
            except APIStatusError as ex:
                if 400 <= ex.status_code < 500:
                    logger.warning(
                        "llm_non_retryable_status_error",
                        attempt_number=attempt,
                        status_code=ex.status_code,
                        error=str(ex),
                        wait_seconds=0,
                    )
                    raise LLMUnavailableError from ex

                if attempt == self.max_attempts:
                    logger.warning(
                        "llm_retry_exhausted",
                        attempt_number=attempt,
                        status_code=ex.status_code,
                        error=str(ex),
                        wait_seconds=0,
                    )
                    raise LLMUnavailableError from ex

                wait_seconds = self._retry_delay(attempt, ex)
                logger.warning(
                    "llm_retry_scheduled",
                    attempt_number=attempt,
                    error=str(ex),
                    wait_seconds=wait_seconds,
                )
                await asyncio.sleep(wait_seconds)
            except Exception as ex:
                logger.exception("llm_request_failed", model=self.model)
                raise LLMUnavailableError from ex

        raise LLMUnavailableError("LLM request failed")

    def stream_message(self, messages: Iterable[MessageParam], **kwargs: Any) -> Any:
        logger.info("llm_stream_started", model=self.model)
        return self.client.messages.stream(
            max_tokens=self.max_tokens,
            model=self.model,
            messages=messages,
            **kwargs
        )

    def _retry_delay(self, attempt: int, ex: Exception) -> float:
        retry_after = self._retry_after_seconds(ex)
        backoff = self.base_delay * 2 ** (attempt - 1) + random.uniform(0, 1)
        if retry_after is None:
            return backoff
        return max(retry_after, backoff)

    @staticmethod
    def _retry_after_seconds(ex: Exception) -> float | None:
        if not isinstance(ex, APIStatusError):
            return None

        retry_after = ex.response.headers.get("retry-after")
        if retry_after is None:
            return None

        try:
            return float(retry_after)
        except Exception:
            return None


llm_client = LLMClient(
    api_key=settings.ANTHROPIC_API_KEY,
    model=settings.ANTHROPIC_MODEL,
    max_tokens=settings.MAX_TOKENS,
    max_attempts=settings.LLM_MAX_ATTEMPTS
)
