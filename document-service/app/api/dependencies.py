from typing import Annotated

from fastapi import Depends

from app.llm.client import AnthropicClient, anthropic_client


def get_llm_client() -> AnthropicClient:
    return anthropic_client


LLMClientDep = Annotated[AnthropicClient, Depends(get_llm_client)]
