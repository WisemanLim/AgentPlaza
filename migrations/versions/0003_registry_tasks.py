"""registry + orchestration: agents · capabilities · tasks · approvals (Epic 4 — D2-01/02/06, D5-06)

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("type", sa.String(24), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="registered"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("builtin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String(16), nullable=False, server_default="zip"),
        sa.Column("trust", sa.String(16), nullable=False, server_default="community"),
        sa.Column("runtime_mode", sa.String(16), nullable=False, server_default="container"),
        sa.Column("endpoint", sa.String(255), nullable=True),
        sa.Column("manifest", sa.JSON, nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("updated_at", TS, nullable=False),
    )
    op.create_table(
        "capabilities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("agent_id", sa.String(64), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("verb", sa.String(64), nullable=False),
        sa.Column("domain", sa.String(120), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("input_schema", sa.JSON, nullable=False),
        sa.Column("human_approval_required", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("keywords", sa.JSON, nullable=False),
        sa.UniqueConstraint("agent_id", "verb", name="uq_capabilities_agent_verb"),
    )
    op.create_index("ix_capabilities_agent_id", "capabilities", ["agent_id"])
    op.create_index("ix_capabilities_domain", "capabilities", ["domain"])
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("principal", sa.String(255), nullable=False),
        sa.Column("principal_role", sa.String(16), nullable=False, server_default="user"),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="running"),
        sa.Column("plan", sa.JSON, nullable=False),
        sa.Column("results", sa.JSON, nullable=False),
        sa.Column("answer", sa.Text, nullable=True),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("ended_at", TS, nullable=True),
    )
    op.create_index("ix_tasks_session_id", "tasks", ["session_id"])
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_id", sa.String(40), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("capability", sa.String(64), nullable=False),
        sa.Column("args", sa.JSON, nullable=False),
        sa.Column("requester", sa.String(255), nullable=False),
        sa.Column("approver", sa.String(255), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("expires_at", TS, nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("decided_at", TS, nullable=True),
    )
    op.create_index("ix_approvals_task_id", "approvals", ["task_id"])


def downgrade() -> None:
    op.drop_table("approvals")
    op.drop_table("tasks")
    op.drop_table("capabilities")
    op.drop_table("agents")
