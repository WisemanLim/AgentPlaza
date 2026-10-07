"""llm: llm_models · llm_routes · llm_usage (Epic 3 — D1-05, D1-06)

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_models",
        sa.Column("id", sa.String(120), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("local", sa.Boolean, nullable=False),
        sa.Column("context", sa.Integer, nullable=False),
        sa.Column("tool_call", sa.Boolean, nullable=False),
        sa.Column("vision", sa.Boolean, nullable=False),
        sa.Column("license", sa.String(64), nullable=False),
        sa.Column("commercial_use", sa.String(16), nullable=False, server_default="allowed"),
        sa.Column("cost_in", sa.Float, nullable=False, server_default="0"),
        sa.Column("cost_out", sa.Float, nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "llm_routes",
        sa.Column("alias", sa.String(80), primary_key=True),
        sa.Column("targets", sa.JSON, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
    )
    op.create_table(
        "llm_usage",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alias", sa.String(80), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("agent_id", sa.String(100), nullable=True),
        sa.Column("principal", sa.String(255), nullable=True),
        sa.Column("data_class", sa.String(4), nullable=False),
        sa.Column("tokens_in", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost", sa.Float, nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("fallback_from", sa.String(120), nullable=True),
        sa.Column("outcome", sa.String(16), nullable=False, server_default="ok"),
    )
    op.create_index("ix_llm_usage_ts", "llm_usage", ["ts"])
    op.create_index("ix_llm_usage_alias", "llm_usage", ["alias"])


def downgrade() -> None:
    op.drop_table("llm_usage")
    op.drop_table("llm_routes")
    op.drop_table("llm_models")
