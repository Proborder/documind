from fastapi import APIRouter

from app.api.dependencies import DBDep, LLMClientDep
from app.core.exceptions import DatabaseNotUnavailableException, DatabaseNotUnavailableHTTPException
from app.schemas.requests import AnalyzeRequest, AnalyzeResponse
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(db: DBDep, llm_client: LLMClientDep, data: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return await DocumentService(db, llm_client).analyze(data)
    except DatabaseNotUnavailableException as ex:
        raise DatabaseNotUnavailableHTTPException from ex
