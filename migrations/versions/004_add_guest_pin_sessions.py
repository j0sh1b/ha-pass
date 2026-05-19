"""Add guest_pin_sessions table for PIN-based access control.

Revision ID: 004
Revises: 003
Create Date: 2025-05-19
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create guest_pin_sessions table for session-based PIN validation
    op.execute("""
        CREATE TABLE IF NOT EXISTS guest_pin_sessions (
            id          TEXT PRIMARY KEY,
            token_id    TEXT NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,
            created_at  INTEGER NOT NULL,
            expires_at  INTEGER NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_guest_pin_sessions_token_id ON guest_pin_sessions(token_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_guest_pin_sessions_expires_at ON guest_pin_sessions(expires_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_guest_pin_sessions_expires_at")
    op.execute("DROP INDEX IF EXISTS idx_guest_pin_sessions_token_id")
    op.execute("DROP TABLE IF EXISTS guest_pin_sessions")
