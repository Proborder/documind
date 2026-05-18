from app.models.requests import RequestsOrm
from app.repositories.base import BaseRepository
from app.schemas.requests import Analyze


class RequestsRepository(BaseRepository):
    model = RequestsOrm
    schema = Analyze
