from typing import Annotated, AsyncGenerator

from fastapi import Depends

from app.core.database import async_session_maker
from app.llm.client import AnthropicClient, anthropic_client
from app.services.db_manager import DBManager


async def get_db() -> AsyncGenerator[DBManager, None]:
    async with DBManager(session_factory=async_session_maker) as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]


def get_llm_client() -> AnthropicClient:
    return anthropic_client


LLMClientDep = Annotated[AnthropicClient, Depends(get_llm_client)]
