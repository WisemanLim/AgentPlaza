"""assistant extensions: llm_models.kind · kb_collections/documents/chunks · memories · files (Epic 15 — D3-04~06, D1-07)

Revision ID: 0009
Revises: 0008
"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column("llm_models", sa.Column("kind", sa.String(16), nullable=False, server_default="chat"))
    op.create_table(
        "kb_collections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("shared", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("data_class", sa.String(4), nullable=False, server_default="L2"),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_table(
        "kb_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("collection_id", sa.String(36), sa.ForeignKey("kb_collections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime", sa.String(100), nullable=False),
        sa.Column("bytes", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ready"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("chunks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_index("ix_kb_documents_collection_id", "kb_documents", ["collection_id"])
    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("collection_id", sa.String(36), nullable=False),
        sa.Column("ord", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("embedding", sa.JSON, nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
    )
    op.create_index("ix_kb_chunks_collection_id", "kb_chunks", ["collection_id"])
    op.create_index("ix_kb_chunks_document_id", "kb_chunks", ["document_id"])
    op.create_table(
        "memories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="manual"),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("updated_at", TS, nullable=False),
    )
    op.create_index("ix_memories_owner", "memories", ["owner"])
    op.create_table(
        "files",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime", sa.String(100), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("bytes", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_index("ix_files_owner", "files", ["owner"])


def downgrade() -> None:
    op.drop_table("files")
    op.drop_table("memories")
    op.drop_table("kb_chunks")
    op.drop_table("kb_documents")
    op.drop_table("kb_collections")
    op.drop_column("llm_models", "kind")
