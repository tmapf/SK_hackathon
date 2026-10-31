"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-10-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offer_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("street", sa.String(length=255)),
        sa.Column("district", sa.String(length=128)),
        sa.Column("city", sa.String(length=128)),
        sa.Column("house_number", sa.String(length=64)),
        sa.Column("unit_number", sa.String(length=64)),
        sa.Column("area_m2", sa.Float()),
        sa.Column("intended_use", sa.Text()),
        sa.Column("development_state", sa.String(length=255)),
        sa.Column("status", sa.String(length=255)),
        sa.Column("starting_rate", sa.Float()),
        sa.Column("starting_price", sa.Float()),
        sa.Column("rental_term", sa.String(length=128)),
        sa.Column("rental_mode", sa.String(length=128)),
        sa.Column("announcement_url", sa.Text()),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("offer_type", "source_id", name="uq_property_offer_source"),
    )
    op.create_index("ix_properties_offer_type", "properties", ["offer_type"])
    op.create_index("ix_properties_source_id", "properties", ["source_id"])
    op.create_index("ix_properties_district", "properties", ["district"])
    op.create_index("ix_properties_is_active", "properties", ["is_active"])

    op.create_table(
        "proposal_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("label_pl", sa.String(length=255), nullable=False),
        sa.Column("label_en", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "source_translations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("source_value", sa.String(length=512), nullable=False),
        sa.Column("value_en", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("field_name", "source_value", name="uq_translation_field_value"),
    )

    op.create_table(
        "administrators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("offer_types", sa.String(length=64), nullable=False),
        sa.Column("properties_upserted", sa.Integer(), server_default="0"),
        sa.Column("properties_skipped", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("proposal_categories.id"),
            nullable=False,
        ),
        sa.Column("proposal_text", sa.Text(), nullable=False),
        sa.Column("email", sa.String(length=255)),
        sa.Column("property_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("submitter_ip_hash", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("suggestions")
    op.drop_table("sync_runs")
    op.drop_table("administrators")
    op.drop_table("source_translations")
    op.drop_table("proposal_categories")
    op.drop_table("properties")
