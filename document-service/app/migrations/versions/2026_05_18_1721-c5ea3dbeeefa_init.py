"""Init

Revision ID: c5ea3dbeeefa
Revises:
Create Date: 2026-05-18 17:21:10.359584

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c5ea3dbeeefa"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("text_hash", sa.String(), nullable=False),
        sa.Column("instruction", sa.String(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "text_hash", "instruction", name="uq_requests_text_hash_instruction"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("requests")
