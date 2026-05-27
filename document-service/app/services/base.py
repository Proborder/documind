from app.llm.client import LLMClient
from app.services.db_manager import DBManager


class BaseService:
    db: DBManager | None

    def __init__(self, db: DBManager | None = None, llm_client: LLMClient | None = None) -> None:
        self.db = db
        self.llm_client = llm_client
