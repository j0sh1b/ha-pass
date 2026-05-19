"""Add new features: scheduled tokens, entity ordering, custom messages, encrypted PIN.

Revision ID: 003
Revises: 002
Create Date: 2025-05-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add starts_at column for scheduled token activation
    op.add_column("tokens", sa.Column("starts_at", sa.Integer(), nullable=True))
    op.create_index("idx_tokens_starts_at", "tokens", ["starts_at"])
    op.execute("UPDATE tokens SET starts_at = created_at WHERE starts_at IS NULL")

    # Add order_index column for entity ordering
    op.add_column(
        "token_entities",
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "idx_token_entities_order", "token_entities", ["token_id", "order_index"]
    )

    # Add custom message columns
    op.add_column(
        "tokens", sa.Column("pre_start_message", sa.Text(), nullable=True)
    )
    op.add_column(
        "tokens", sa.Column("expired_message", sa.Text(), nullable=True)
    )

    # Add encrypted PIN column
    op.add_column(
        "tokens", sa.Column("pin_encrypted", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    # Drop encrypted PIN column
    op.drop_column("tokens", "pin_encrypted")

    # Drop custom message columns
    op.drop_column("tokens", "expired_message")
    op.drop_column("tokens", "pre_start_message")

    # Drop order_index column and index
    op.drop_index("idx_token_entities_order", table_name="token_entities")
    op.drop_column("token_entities", "order_index")

    # Drop starts_at column and index
    op.drop_index("idx_tokens_starts_at", table_name="tokens")
    op.drop_column("tokens", "starts_at")
