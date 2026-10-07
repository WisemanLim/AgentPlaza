"""market commerce & publishers: publishers · market_listings · market_releases · licenses · license_seats ·
purchases · market_downloads (Epic 18 — D6-05, D6-06, D6-07)

Revision ID: 0012
Revises: 0011
"""
import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "publishers",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("url", sa.String(255), nullable=True),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("members", sa.JSON, nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_table(
        "market_listings",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("origin", sa.String(80), nullable=False),
        sa.Column("publisher_id", sa.String(64), nullable=True),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("updated_at", TS, nullable=False),
    )
    op.create_index("ix_market_listings_publisher_id", "market_listings", ["publisher_id"])
    op.create_table(
        "market_releases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("listing_id", sa.String(64), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("publisher_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("artifact", sa.String(255), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("listing", sa.JSON, nullable=False),
        sa.Column("gate", sa.JSON, nullable=False),
        sa.Column("submitted_by", sa.String(255), nullable=False),
        sa.Column("reviewed_by", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("reviewed_at", TS, nullable=True),
        sa.UniqueConstraint("listing_id", "version"),
    )
    op.create_index("ix_market_releases_listing_id", "market_releases", ["listing_id"])
    op.create_index("ix_market_releases_publisher_id", "market_releases", ["publisher_id"])
    op.create_table(
        "licenses",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("listing_id", sa.String(64), nullable=False),
        sa.Column("token", sa.Text, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("issuer", sa.String(64), nullable=False),
        sa.Column("seats", sa.Integer, nullable=False, server_default="1"),
        sa.Column("expires_at", TS, nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("registered_by", sa.String(255), nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_index("ix_licenses_listing_id", "licenses", ["listing_id"])
    op.create_table(
        "license_seats",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("license_id", sa.String(64), sa.ForeignKey("licenses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("holder", sa.String(255), nullable=False),
        sa.Column("assigned_at", TS, nullable=False),
        sa.UniqueConstraint("license_id", "holder"),
    )
    op.create_index("ix_license_seats_license_id", "license_seats", ["license_id"])
    op.create_table(
        "purchases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("listing_id", sa.String(64), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("buyer", sa.String(255), nullable=False),
        sa.Column("seats", sa.Integer, nullable=False),
        sa.Column("months", sa.Integer, nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("adapter", sa.String(32), nullable=False),
        sa.Column("adapter_ref", sa.String(120), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("license_id", sa.String(64), nullable=True),
        sa.Column("receipt", sa.JSON, nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_index("ix_purchases_listing_id", "purchases", ["listing_id"])
    op.create_table(
        "market_downloads",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("listing_id", sa.String(64), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("at", TS, nullable=False),
    )
    op.create_index("ix_market_downloads_listing_id", "market_downloads", ["listing_id"])


def downgrade() -> None:
    for t in ("market_downloads", "purchases", "license_seats", "licenses", "market_releases", "market_listings",
              "publishers"):
        op.drop_table(t)
