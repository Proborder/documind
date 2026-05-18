from datetime import datetime
import uuid

from sqlalchemy import Text, UniqueConstraint, func
from sqlalchemy.orm import mapped_column, Mapped

from app.core.database import Base


class RequestsOrm(Base):
    __tablename__ = "requests"
    __table_args__ = (
        UniqueConstraint("text_hash", "instruction", name="uq_requests_text_hash_instruction"),
    )

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    text_hash: Mapped[str]
    instruction: Mapped[str]
    response: Mapped[str] = mapped_column(Text)
    model: Mapped[str]
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
