"""assistant: sessions · messages (Epic 5 — D3-02)

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("agent_scope", sa.String(64), nullable=True),
        sa.Column("folder", sa.String(100), nullable=True),
        sa.Column("data_class", sa.String(4), nullable=False, server_default="L2"),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("updated_at", TS, nullable=False),
        sa.Column("archived_at", TS, nullable=True),
    )
    op.create_index("ix_sessions_owner", "sessions", ["owner"])
    op.create_index("ix_sessions_updated_at", "sessions", ["updated_at"])
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False, server_default="text"),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("task_id", sa.String(36), nullable=True),
        sa.Column("meta", sa.JSON, nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_index("ix_messages_session_id", "messages", ["session_id"])


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("sessions")
