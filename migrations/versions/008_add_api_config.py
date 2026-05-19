"""Add API configuration table.

Revision ID: 008
Revises: 007
Create Date: 2025-05-19
"""
from typing import Sequence, Union

from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS api_config (
            id          INTEGER PRIMARY KEY CHECK (id = 1),
            enabled     INTEGER NOT NULL DEFAULT 0,
            token_hash  TEXT
        )
    """)
    # Insert default row
    op.execute("INSERT INTO api_config (id, enabled) VALUES (1, 0)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS api_config")
