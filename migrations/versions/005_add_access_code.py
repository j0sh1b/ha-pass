"""Add access_code column to tokens table.

Revision ID: 005
Revises: 004
Create Date: 2025-05-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add access_code column WITHOUT UNIQUE constraint first
    # SQLite cannot add UNIQUE columns to tables with existing data
    op.add_column("tokens", sa.Column("access_code", sa.Text(), nullable=True))
    
    # Create a partial unique index that only enforces uniqueness on non-NULL values
    # This allows multiple tokens to have NULL access_code while ensuring
    # that any tokens WITH access_codes have unique values
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_tokens_access_code "
        "ON tokens(access_code) WHERE access_code IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_tokens_access_code")
    op.drop_column("tokens", "access_code")
