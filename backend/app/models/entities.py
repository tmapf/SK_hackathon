from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("offer_type", "source_id", name="uq_property_offer_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    offer_type: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[int] = mapped_column(Integer, index=True)
    street: Mapped[str | None] = mapped_column(String(255))
    district: Mapped[str | None] = mapped_column(String(128), index=True)
    city: Mapped[str | None] = mapped_column(String(128))
    house_number: Mapped[str | None] = mapped_column(String(64))
    unit_number: Mapped[str | None] = mapped_column(String(64))
    area_m2: Mapped[float | None] = mapped_column(Float)
    intended_use: Mapped[str | None] = mapped_column(Text)
    development_state: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(255))
    starting_rate: Mapped[float | None] = mapped_column(Float)
    starting_price: Mapped[float | None] = mapped_column(Float)
    rental_term: Mapped[str | None] = mapped_column(String(128))
    rental_mode: Mapped[str | None] = mapped_column(String(128))
    announcement_url: Mapped[str | None] = mapped_column(Text)
    longitude: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float] = mapped_column(Float)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    suggestions: Mapped[list[Suggestion]] = relationship(back_populates="property")


class ProposalCategory(Base):
    __tablename__ = "proposal_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label_pl: Mapped[str] = mapped_column(String(255))
    label_en: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    suggestions: Mapped[list[Suggestion]] = relationship(back_populates="category")


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("proposal_categories.id"), index=True
    )
    proposal_text: Mapped[str] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(255))
    property_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    submitter_ip_hash: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    property: Mapped[Property] = relationship(back_populates="suggestions")
    category: Mapped[ProposalCategory] = relationship(back_populates="suggestions")


class SourceTranslation(Base):
    __tablename__ = "source_translations"
    __table_args__ = (
        UniqueConstraint("field_name", "source_value", name="uq_translation_field_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    field_name: Mapped[str] = mapped_column(String(64), index=True)
    source_value: Mapped[str] = mapped_column(String(512))
    value_en: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Administrator(Base):
    __tablename__ = "administrators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    offer_types: Mapped[str] = mapped_column(String(64))
    properties_upserted: Mapped[int] = mapped_column(Integer, default=0)
    properties_skipped: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
