from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


OfferType = Literal["wynajem", "sprzedaz"]


class MessageOut(BaseModel):
    message: str


class PublicConfigOut(BaseModel):
    turnstile_site_key: str
    tile_url: str
    tile_attribution: str
    privacy_policy_url: str
    contact_email: str
    last_successful_sync_at: datetime | None


class PropertyPublicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_type: OfferType
    source_id: int
    street: str | None
    district: str | None
    city: str | None
    house_number: str | None
    unit_number: str | None
    area_m2: float | None
    intended_use: str | None
    development_state: str | None
    longitude: float
    latitude: float
    address_label: str


class PropertyAdminOut(PropertyPublicOut):
    status: str | None
    starting_rate: float | None
    starting_price: float | None
    rental_term: str | None
    rental_mode: str | None
    announcement_url: str | None
    is_active: bool
    synced_at: datetime


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label_pl: str
    label_en: str
    sort_order: int
    is_active: bool


class CategoryCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    label_pl: str = Field(min_length=1, max_length=255)
    label_en: str = Field(min_length=1, max_length=255)
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    label_pl: str | None = Field(default=None, min_length=1, max_length=255)
    label_en: str | None = Field(default=None, min_length=1, max_length=255)
    sort_order: int | None = None
    is_active: bool | None = None


class SuggestionCreate(BaseModel):
    property_id: int
    category_id: int
    proposal_text: str = Field(min_length=10, max_length=1000)
    email: EmailStr | None = None
    turnstile_token: str = Field(default="demo-bypass", max_length=2048)
    website: str | None = Field(default="", max_length=200, description="Honeypot")


class SuggestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: int
    category_id: int
    proposal_text: str
    email: str | None
    property_snapshot: dict[str, Any]
    created_at: datetime
    category: CategoryOut | None = None


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class AdminOut(BaseModel):
    id: int
    username: str


class TranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field_name: str
    source_value: str
    value_en: str


class TranslationUpsert(BaseModel):
    field_name: str = Field(min_length=1, max_length=64)
    source_value: str = Field(min_length=1, max_length=512)
    value_en: str = Field(min_length=1, max_length=512)


class SyncRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    offer_types: str
    properties_upserted: int
    properties_skipped: int
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class PopularPropertyOut(BaseModel):
    property_id: int
    offer_type: OfferType
    address_label: str
    district: str | None
    area_m2: float | None
    intended_use: str | None
    development_state: str | None
    longitude: float
    latitude: float
    suggestion_count: int
    announcement_url: str | None = None
