"""organizations & deploy scope: orgs · org_members · org_groups · group_members · agent_scopes
(Epic 23 — PRD Q7·Q12, UI K02·FL-07). 기본 조직(default)을 만들고 기존 사용자를 구성원으로 옮긴다.

Revision ID: 0013
Revises: 0012
"""
import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "orgs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_table(
        "org_members",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_id", sa.String(64), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="member"),
        sa.UniqueConstraint("org_id", "user_id"),
    )
    op.create_index("ix_org_members_org_id", "org_members", ["org_id"])
    op.create_index("ix_org_members_user_id", "org_members", ["user_id"])
    op.create_table(
        "org_groups",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(64), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.UniqueConstraint("org_id", "name"),
    )
    op.create_index("ix_org_groups_org_id", "org_groups", ["org_id"])
    op.create_table(
        "group_members",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("org_groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("group_id", "user_id"),
    )
    op.create_index("ix_group_members_group_id", "group_members", ["group_id"])
    op.create_index("ix_group_members_user_id", "group_members", ["user_id"])
    op.create_table(
        "agent_scopes",
        sa.Column("agent_id", sa.String(64), primary_key=True),
        sa.Column("org_id", sa.String(64), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(8), nullable=False),
        sa.Column("ids", sa.JSON, nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=False),
        sa.Column("updated_at", TS, nullable=False),
    )
    # 기본 조직 + 기존 사용자 이관(동작 변화 없음: 범위 행이 없는 에이전트는 모두에게 보인다)
    op.execute(sa.text("INSERT INTO orgs (id, name, created_at) VALUES ('default', '기본 조직', CURRENT_TIMESTAMP)"))
    op.execute(sa.text("INSERT INTO org_members (org_id, user_id, role) SELECT 'default', id, 'member' FROM users"))


def downgrade() -> None:
    for t in ("agent_scopes", "group_members", "org_groups", "org_members", "orgs"):
        op.drop_table(t)
