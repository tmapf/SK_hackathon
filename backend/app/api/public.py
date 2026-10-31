from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import ProposalCategory, Property, Suggestion
from app.api.deps import get_client_ip
from app.schemas.common import (
    CategoryOut,
    MessageOut,
    PropertyPublicOut,
    PublicConfigOut,
    SuggestionCreate,
    TranslationOut,
)
from app.security.rate_limit import suggestion_limiter
from app.security.sessions import hash_ip
from app.services.properties import (
    filtered_properties_query,
    list_address_suggestions,
    list_districts,
    properties_to_geojson,
    property_public_dict,
    property_snapshot,
    translation_map,
)
from app.services.sync import latest_successful_sync
from app.services.turnstile import verify_turnstile

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(select(1))
    return {"status": "ok"}


@router.get("/config", response_model=PublicConfigOut)
def public_config(db: Session = Depends(get_db)) -> PublicConfigOut:
    settings = get_settings()
    latest = latest_successful_sync(db)
    return PublicConfigOut(
        turnstile_site_key=settings.turnstile_site_key,
        tile_url=settings.tile_url,
        tile_attribution=settings.tile_attribution,
        privacy_policy_url=settings.privacy_policy_url,
        contact_email=settings.contact_email,
        last_successful_sync_at=latest.finished_at if latest else None,
    )


@router.get("/properties")
def list_properties(
    offer_type: str | None = Query(default=None, pattern="^(wynajem|sprzedaz)$"),
    district: str | None = None,
    q: str | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    format: str = Query(default="geojson", pattern="^(geojson|json)$"),
    db: Session = Depends(get_db),
):
    stmt = filtered_properties_query(
        offer_type=offer_type,
        district=district,
        q=q,
        min_area=min_area,
        max_area=max_area,
    )
    rows = list(db.scalars(stmt).all())
    if format == "json":
        return [PropertyPublicOut(**property_public_dict(row)) for row in rows]
    return properties_to_geojson(rows)


@router.get("/properties/{property_id}", response_model=PropertyPublicOut)
def get_property(property_id: int, db: Session = Depends(get_db)) -> PropertyPublicOut:
    row = db.get(Property, property_id)
    if row is None or not row.is_active:
        raise HTTPException(status_code=404, detail="Property not found")
    return PropertyPublicOut(**property_public_dict(row))


@router.get("/districts")
def districts(
    offer_type: str | None = Query(default=None, pattern="^(wynajem|sprzedaz)$"),
    db: Session = Depends(get_db),
) -> list[str]:
    return list_districts(db, offer_type=offer_type)


@router.get("/address-suggestions")
def address_suggestions(
    q: str = Query(min_length=1, max_length=120),
    offer_type: str | None = Query(default=None, pattern="^(wynajem|sprzedaz)$"),
    limit: int = Query(default=8, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[dict]:
    return list_address_suggestions(
        db,
        q=q,
        offer_type=offer_type,
        limit=limit,
    )


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)) -> list[ProposalCategory]:
    return list(
        db.scalars(
            select(ProposalCategory)
            .where(ProposalCategory.is_active.is_(True))
            .order_by(ProposalCategory.sort_order.asc(), ProposalCategory.id.asc())
        ).all()
    )


@router.get("/translations")
def translations(db: Session = Depends(get_db)) -> dict[str, dict[str, str]]:
    return translation_map(db)


@router.post("/suggestions", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def create_suggestion(
    payload: SuggestionCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageOut:
    settings = get_settings()
    client_ip = get_client_ip(request)

    # Honeypot: reject if filled
    if payload.website:
        raise HTTPException(status_code=400, detail="Invalid submission")

    if not suggestion_limiter.allow(
        f"suggest:{client_ip}",
        settings.suggestion_rate_limit_per_hour,
        3600,
    ):
        raise HTTPException(status_code=429, detail="Too many suggestions from this address")

    if not await verify_turnstile(payload.turnstile_token, client_ip):
        raise HTTPException(status_code=400, detail="CAPTCHA verification failed")

    property_row = db.get(Property, payload.property_id)
    if property_row is None or not property_row.is_active:
        raise HTTPException(status_code=404, detail="Property not found")

    category = db.get(ProposalCategory, payload.category_id)
    if category is None or not category.is_active:
        raise HTTPException(status_code=400, detail="Invalid category")

    suggestion = Suggestion(
        property_id=property_row.id,
        category_id=category.id,
        proposal_text=payload.proposal_text.strip(),
        email=str(payload.email) if payload.email else None,
        property_snapshot=property_snapshot(property_row),
        submitter_ip_hash=hash_ip(client_ip),
    )
    db.add(suggestion)
    db.commit()
    return MessageOut(message="Suggestion submitted successfully")
