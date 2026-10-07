"""AG-UI stream log: run_events (Epic 16 — D7-06, NFR-P4 재연결 후 재개)

Revision ID: 0010
Revises: 0009
"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "run_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("stream_id", sa.String(36), nullable=False),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("stream_id", "seq", name="uq_run_events_stream_seq"),
    )
    op.create_index("ix_run_events_stream_id", "run_events", ["stream_id"])


def downgrade() -> None:
    op.drop_table("run_events")
