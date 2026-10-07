"""observability & evaluation: trace_spans · eval_suites · eval_runs (Epic 17 — D10-04, D10-05)

Revision ID: 0011
Revises: 0010
"""
import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "trace_spans",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("trace_id", sa.String(32), nullable=False),
        sa.Column("span_id", sa.String(16), nullable=False),
        sa.Column("parent_id", sa.String(16), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("start", TS, nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=False),
        sa.Column("status", sa.String(8), nullable=False),
        sa.Column("attributes", sa.JSON, nullable=False),
    )
    op.create_index("ix_trace_spans_trace_id", "trace_spans", ["trace_id"])
    op.create_index("ix_trace_spans_start", "trace_spans", ["start"])
    op.create_table(
        "eval_suites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("agent_scope", sa.String(64), nullable=True),
        sa.Column("cases", sa.JSON, nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("suite_id", sa.String(36), sa.ForeignKey("eval_suites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("passed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("score", sa.Float, nullable=False, server_default="0"),
        sa.Column("results", sa.JSON, nullable=False),
        sa.Column("started_by", sa.String(255), nullable=False),
        sa.Column("started_at", TS, nullable=False),
        sa.Column("finished_at", TS, nullable=True),
    )
    op.create_index("ix_eval_runs_suite_id", "eval_runs", ["suite_id"])


def downgrade() -> None:
    op.drop_table("eval_runs")
    op.drop_table("eval_suites")
    op.drop_table("trace_spans")
