import uuid

from fastapi import APIRouter

from app.api.dependencies import DBDep
from app.core.exceptions import (
    DatabaseNotUnavailableException,
    DatabaseNotUnavailableHTTPException,
    RequestNotFoundException,
    RequestNotFoundHTTPException,
)
from app.schemas.requests import Analyze
from app.services.requests import RequestsService

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("/{request_id}", response_model=Analyze)
async def get_request(db: DBDep, request_id: uuid.UUID) -> Analyze:
    try:
        return await RequestsService(db).get_request(request_id)
    except RequestNotFoundException as ex:
        raise RequestNotFoundHTTPException from ex
    except DatabaseNotUnavailableException as ex:
        raise DatabaseNotUnavailableHTTPException from ex
