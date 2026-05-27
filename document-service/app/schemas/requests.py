import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AnalyzeRequest(BaseModel):
    text: str
    instruction: str


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int


class AnalyzeResponse(BaseModel):
    analysis: dict
    model: str
    usage: Usage
    request_id: str


class StreamDeltaEvent(BaseModel):
    type: Literal["delta"] = "delta"
    text: str


class StreamDoneEvent(BaseModel):
    type: Literal["done"] = "done"
    usage: Usage


class StreamErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


class AnalyzeAdd(BaseModel):
    text_hash: str
    instruction: str
    response: str
    model: str
    input_tokens: int
    output_tokens: int


class Analyze(AnalyzeAdd):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
