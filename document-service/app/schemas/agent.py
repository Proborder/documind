from typing import Any

from pydantic import BaseModel


class AgentRequest(BaseModel):
    query: str
    document_text: str


class AgentToolCall(BaseModel):
    name: str
    input: dict[str, Any]
    result: Any


class AgentResponse(BaseModel):
    answer: str
    tools_called: list[AgentToolCall]
    iterations: int
    truncated: bool | None = None
