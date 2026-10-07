"""supply chain trust: trusted_keys · agent_versions 서명·SBOM·취약점 (Epic 12 — D4-06, D5-03, D5-04)

Revision ID: 0006
Revises: 0005
"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "trusted_keys",
        sa.Column("kid", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("publisher_id", sa.String(64), nullable=True),
        sa.Column("public_pem", sa.Text, nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("revoked_at", TS, nullable=True),
    )
    op.create_index("ix_trusted_keys_publisher_id", "trusted_keys", ["publisher_id"])
    op.add_column("agent_versions", sa.Column("signer", sa.String(64), nullable=True))
    op.add_column("agent_versions", sa.Column("sbom_ref", sa.String(255), nullable=True))
    op.add_column("agent_versions", sa.Column("vulns", sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("agent_versions", "vulns")
    op.drop_column("agent_versions", "sbom_ref")
    op.drop_column("agent_versions", "signer")
    op.drop_table("trusted_keys")
