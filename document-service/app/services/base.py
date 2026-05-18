from app.llm.client import AnthropicClient
from app.services.db_manager import DBManager


class BaseService:
    db: DBManager | None

    def __init__(self, db: DBManager | None = None, llm_client: AnthropicClient | None = None) -> None:
        self.db = db
        self.llm_client = llm_client
