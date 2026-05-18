import socket
import uuid

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ObjectNotFoundException, RequestNotFoundException, DatabaseNotUnavailableException
from app.core.logger import logger
from app.schemas.requests import Analyze
from app.services.base import BaseService


class RequestsService(BaseService):
    async def get_request(self, request_id: uuid.UUID) -> Analyze | None:
        try:
            data = await self.db.requests.get_one(id=request_id)
            return data
        except ObjectNotFoundException as ex:
            raise RequestNotFoundException from ex
        except (SQLAlchemyError, socket.error) as ex:
            logger.error("Database connection error during fetch", error=str(ex))
            raise DatabaseNotUnavailableException from ex
