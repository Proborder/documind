import hashlib
import json
import socket

from anthropic.types import MessageParam
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import DatabaseNotUnavailableException
from app.core.logger import logger
from app.core.redis_conn import redis_manager
from app.schemas.requests import AnalyzeAdd, AnalyzeRequest, AnalyzeResponse, Usage
from app.services.base import BaseService


class DocumentService(BaseService):
    async def analyze(self, data: AnalyzeRequest) -> AnalyzeResponse:
        text_hash = hashlib.sha256(data.text.encode("utf-8")).hexdigest()
        instruction_hash = hashlib.sha256(data.instruction.encode("utf-8")).hexdigest()

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
                instruction=data.instruction
            )
        except (SQLAlchemyError, socket.error) as ex:
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
            f"Instruction:\n{data.instruction}\n\n"
            f"Document text:\n{data.text}"
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
                instruction=data.instruction,
                response=analysis,
                model=llm_response.model,
                input_tokens=llm_response.usage.input_tokens,
                output_tokens=llm_response.usage.output_tokens
            )
            saved_request = await self.db.requests.add(add_data)
            await self.db.commit()
        except (SQLAlchemyError, socket.error) as ex:
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

    @staticmethod
    def _extract_text(content) -> str:
        analysis = ""
        for block in content:
            if getattr(block, "type", None) == "text":
                analysis += block.text
        return analysis
