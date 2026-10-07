"""notifications & status (Epic 19 — D10-07 알림·상태, UI B03): notifications · notification_reads

Revision ID: 0014
Revises: 0013
"""
import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(8), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("resource", sa.String(200), nullable=True),
        sa.Column("audience", sa.String(255), nullable=False),
        sa.Column("dedup_key", sa.String(255), nullable=False),
        sa.Column("deliveries", sa.JSON, nullable=True),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_index("ix_notifications_kind", "notifications", ["kind"])
    op.create_index("ix_notifications_dedup_key", "notifications", ["dedup_key"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_table(
        "notification_reads",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("notification_id", sa.Integer, sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reader", sa.String(255), nullable=False),
        sa.Column("read_at", TS, nullable=False),
        sa.UniqueConstraint("notification_id", "reader"),
    )
    op.create_index("ix_notification_reads_notification_id", "notification_reads", ["notification_id"])
    op.create_index("ix_notification_reads_reader", "notification_reads", ["reader"])


def downgrade() -> None:
    op.drop_table("notification_reads")
    op.drop_table("notifications")
