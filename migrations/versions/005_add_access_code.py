"""Add access_code column to tokens table.

Revision ID: 005
Revises: 004
Create Date: 2025-05-19
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add access_code column to tokens table
    op.execute("ALTER TABLE tokens ADD COLUMN access_code TEXT UNIQUE")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tokens_access_code ON tokens(access_code)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_tokens_access_code")
    op.execute("ALTER TABLE tokens DROP COLUMN access_code")
