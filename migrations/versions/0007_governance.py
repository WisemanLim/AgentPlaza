"""governance: secrets(암호화 저장소) · tasks.data_class (Epic 13 — D9-04, D9-05)

Revision ID: 0007
Revises: 0006
"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "secrets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("scope", sa.String(80), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("ciphertext", sa.Text, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("updated_at", TS, nullable=False),
        sa.UniqueConstraint("scope", "name", name="uq_secrets_scope_name"),
    )
    op.add_column("tasks", sa.Column("data_class", sa.String(4), nullable=False, server_default="L2"))


def downgrade() -> None:
    op.drop_column("tasks", "data_class")
    op.drop_table("secrets")
