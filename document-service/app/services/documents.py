import hashlib
import json
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Any

from anthropic.types import MessageParam
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import (
    DatabaseNotUnavailableException,
    StructuredOutputValidationException,
    ToolUseNotFoundException,
    UnknownExtractionSchemaException
)
from app.core.logger import logger
from app.core.redis_conn import redis_manager
from app.schemas.extraction import ContractData, ExtractRequest, ExtractResponse, InvoiceData
from app.schemas.requests import (
    AnalyzeAdd,
    AnalyzeRequest,
    AnalyzeResponse,
    StreamDeltaEvent,
    StreamDoneEvent,
    StreamErrorEvent,
    Usage
)
from app.services.base import BaseService


class DocumentService(BaseService):
    extraction_tools: dict[str, dict[str, Any]] = {
        "invoice": {
            "model": InvoiceData,
            "name": "extract_invoice",
            "description": "Extract structured invoice data from document text",
        },
        "contract": {
            "model": ContractData,
            "name": "extract_contract",
            "description": "Extract structured contract data from document text",
        },
    }

    async def analyze(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        text_hash = hashlib.sha256(payload.text.encode("utf-8")).hexdigest()
        instruction_hash = hashlib.sha256(payload.instruction.encode("utf-8")).hexdigest()

        key = f"requests:analyze:{text_hash}:{instruction_hash}"
        request_from_cache = None

        try:
            request_from_cache = await redis_manager.get(key)
        except (RedisError, ConnectionError) as ex:
            logger.warning("Redis is unavailable", error=str(ex))

        if request_from_cache:
            payload = json.loads(request_from_cache)
            logger.info("request_returned_from_cache", cache_key=key)
            return AnalyzeResponse.model_validate(payload)

        try:
            existing_request = await self.db.requests.get_one_or_none(
                text_hash=text_hash,
                instruction=payload.instruction
            )
        except (SQLAlchemyError, OSError) as ex:
            logger.error("Database connection error during request lookup", error=str(ex))
            raise DatabaseNotUnavailableException from ex

        if existing_request:
            response = AnalyzeResponse(
                analysis=existing_request.response,
                model=existing_request.model,
                usage=Usage(
                    input_tokens=existing_request.input_tokens,
                    output_tokens=existing_request.output_tokens,
                ),
                request_id=str(existing_request.id)
            )

            try:
                await redis_manager.set(key, response.model_dump_json(), settings.CACHE_TTL_SECONDS)
            except (RedisError, ConnectionError) as ex:
                logger.warning("Redis is unavailable", error=str(ex))

            return response

        system_prompt = (
            "You are a precise document analyst. "
            "Extract key points, risks, ambiguities, and actionable recommendations. "
            "Keep the output concise and structured."
        )
        user_prompt = (
            f"Instruction:\n{payload.instruction}\n\n"
            f"Document text:\n{payload.text}"
        )
        messages: list[MessageParam] = [{"role": "user", "content": user_prompt}]

        llm_response = await self.llm_client.create_message(
            messages=messages,
            system=system_prompt
        )
        analysis = self._extract_text(llm_response.content)
        try:
            add_data = AnalyzeAdd(
                text_hash=text_hash,
                instruction=payload.instruction,
                response=analysis,
                model=llm_response.model,
                input_tokens=llm_response.usage.input_tokens,
                output_tokens=llm_response.usage.output_tokens
            )
            saved_request = await self.db.requests.add(add_data)
            await self.db.commit()
        except (SQLAlchemyError, OSError) as ex:
            logger.error("Database connection error during request save", error=str(ex))
            raise DatabaseNotUnavailableException from ex

        response = AnalyzeResponse(
            analysis=analysis,
            model=saved_request.model,
            usage=Usage(
                input_tokens=saved_request.input_tokens,
                output_tokens=saved_request.output_tokens,
            ),
            request_id=str(saved_request.id)
        )

        try:
            await redis_manager.set(key, response.model_dump_json(), settings.CACHE_TTL_SECONDS)
        except (RedisError, ConnectionError) as ex:
            logger.warning("Redis is unavailable", error=str(ex))

        return response

    async def analyze_stream(
        self,
        payload: AnalyzeRequest,
        is_disconnected: Callable[[], Awaitable[bool]]
    ) -> AsyncGenerator[str, None]:
        system_prompt = (
            "You are a precise document analyst. "
            "Extract key points, risks, ambiguities, and actionable recommendations. "
            "Keep the output concise and structured."
        )
        user_prompt = (
            f"Instruction:\n{payload.instruction}\n\n"
            f"Document text:\n{payload.text}"
        )
        messages: list[MessageParam] = [{"role": "user", "content": user_prompt}]

        try:
            async with self.llm_client.stream_message(
                messages=messages,
                system=system_prompt
            ) as stream:
                async for text in stream.text_stream:
                    if await is_disconnected():
                        logger.info("client_disconnected_from_stream")
                        return

                    event = StreamDeltaEvent(text=text)
                    yield f"data: {event.model_dump_json()}\n\n"

                final_message = await stream.get_final_message()
                event = StreamDoneEvent(
                    usage=Usage(
                        input_tokens=final_message.usage.input_tokens,
                        output_tokens=final_message.usage.output_tokens,
                    )
                )
                yield f"data: {event.model_dump_json()}\n\n"
                logger.info("llm_stream_finished", model=self.llm_client.model)
        except Exception as ex:
            logger.exception("llm_stream_failed")
            event = StreamErrorEvent(message=str(ex))
            yield f"data: {event.model_dump_json()}\n\n"

    async def extract(self, data: ExtractRequest) -> ExtractResponse:
        tool_config = self.extraction_tools.get(data.schema_name)
        if tool_config is None:
            raise UnknownExtractionSchemaException

        schema_model = tool_config["model"]
        tool_name = str(tool_config["name"])
        tool = {
            "name": tool_name,
            "description": tool_config["description"],
            "input_schema": schema_model.model_json_schema()
        }
        system_prompt = (
            "You extract structured data from documents. "
            "Use the provided tool only. "
            "If a nullable field is not present in the document, set it to null. "
            "If a list field has no values, return an empty list."
        )
        messages: list[MessageParam] = [
            {
                "role": "user",
                "content": f"Extract structured data from this document:\n\n{data.text}"
            }
        ]

        llm_response = await self.llm_client.create_message(
            messages=messages,
            system=system_prompt,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name}
        )

        if llm_response.stop_reason != "tool_use":
            raise ToolUseNotFoundException

        for block in llm_response.content:
            if (
                getattr(block, "type", None) == "tool_use"
                and getattr(block, "name", None) == tool_name
            ):
                try:
                    return schema_model.model_validate(block.input)
                except ValidationError as ex:
                    logger.warning("structured_output_validation_failed", error=str(ex))
                    raise StructuredOutputValidationException from ex

        raise ToolUseNotFoundException

    @staticmethod
    def _extract_text(content) -> str:
        analysis = ""
        for block in content:
            if getattr(block, "type", None) == "text":
                analysis += block.text
        return analysis
