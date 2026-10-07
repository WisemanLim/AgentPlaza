"""registry pipeline: agent_versions · installs (Epic 6 — D5-01/02/05/06/07)

Revision ID: 0005
Revises: 0004
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "agent_versions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("artifact", sa.String(255), nullable=False),
        sa.Column("signature_ok", sa.Boolean, nullable=True),
        sa.Column("license_grade", sa.String(4), nullable=True),
        sa.Column("current", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("installed_at", TS, nullable=False),
        sa.Column("installed_by", sa.String(255), nullable=False),
        sa.UniqueConstraint("agent_id", "version", name="uq_agent_versions_agent_version"),
    )
    op.create_index("ix_agent_versions_agent_id", "agent_versions", ["agent_id"])
    op.create_table(
        "installs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_id", sa.String(64), nullable=True),
        sa.Column("version", sa.String(40), nullable=True),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("source_ref", sa.String(500), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("steps", sa.JSON, nullable=False),
        sa.Column("warnings", sa.JSON, nullable=False),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("env", sa.JSON, nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("updated_at", TS, nullable=False),
    )
    op.create_index("ix_installs_agent_id", "installs", ["agent_id"])


def downgrade() -> None:
    op.drop_table("installs")
    op.drop_table("agent_versions")
