from fastapi import APIRouter

from app.api.dependencies import DBDep, LLMClientDep
from app.core.exceptions import (
    DatabaseNotUnavailableException,
    DatabaseNotUnavailableHTTPException,
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


@router.post("/extract", response_model=ExtractResponse)
async def extract(data: ExtractRequest, llm_client: LLMClientDep) -> ExtractResponse:
    try:
        return await DocumentService(llm_client=llm_client).extract(data)
    except UnknownExtractionSchemaException as ex:
        raise UnknownExtractionSchemaHTTPException from ex
    except ToolUseNotFoundException as ex:
        raise ToolUseNotFoundHTTPException from ex
    except StructuredOutputValidationException as ex:
        raise StructuredOutputValidationHTTPException from ex
