"""channels & embed (Epic 25 — D3-07 채널·임베드, UI C07): channels · channel_threads

Revision ID: 0015
Revises: 0014
"""
import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("config", sa.JSON, nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_table(
        "channel_threads",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("channel_id", sa.String(40), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("updated_at", TS, nullable=False),
        sa.UniqueConstraint("channel_id", "external_id"),
    )
    op.create_index("ix_channel_threads_channel_id", "channel_threads", ["channel_id"])


def downgrade() -> None:
    op.drop_table("channel_threads")
    op.drop_table("channels")
