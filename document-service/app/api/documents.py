from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import DBDep, LLMClientDep
from app.core.exceptions import (
    DatabaseNotUnavailableException,
    DatabaseNotUnavailableHTTPException,
    LLMProviderException,
    LLMProviderHTTPException,
    StructuredOutputValidationException,
    StructuredOutputValidationHTTPException,
    ToolUseNotFoundException,
    ToolUseNotFoundHTTPException,
    UnknownExtractionSchemaException,
    UnknownExtractionSchemaHTTPException,
)
from app.schemas.extraction import ExtractRequest, ExtractResponse
from app.schemas.requests import AnalyzeRequest, AnalyzeResponse
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(db: DBDep, llm_client: LLMClientDep, payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return await DocumentService(db, llm_client).analyze(payload)
    except DatabaseNotUnavailableException as ex:
        raise DatabaseNotUnavailableHTTPException from ex
    except LLMProviderException as ex:
        raise LLMProviderHTTPException from ex


@router.post("/analyze/stream")
async def analyze_stream(
    request: Request,
    llm_client: LLMClientDep,
    payload: AnalyzeRequest
) -> StreamingResponse:
    return StreamingResponse(
        DocumentService(llm_client=llm_client).analyze_stream(
            payload=payload,
            is_disconnected=request.is_disconnected
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/extract", response_model=ExtractResponse)
async def extract(data: ExtractRequest, llm_client: LLMClientDep) -> ExtractResponse:
    try:
        return await DocumentService(llm_client=llm_client).extract(data)
    except LLMProviderException as ex:
        raise LLMProviderHTTPException from ex
    except UnknownExtractionSchemaException as ex:
        raise UnknownExtractionSchemaHTTPException from ex
    except ToolUseNotFoundException as ex:
        raise ToolUseNotFoundHTTPException from ex
    except StructuredOutputValidationException as ex:
        raise StructuredOutputValidationHTTPException from ex
