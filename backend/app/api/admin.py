from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_client_ip, get_current_admin, require_csrf
from app.config import get_settings
from app.database import get_db
from app.models import Administrator, ProposalCategory, Property, SourceTranslation, Suggestion, SyncRun
from app.schemas.common import (
    AdminOut,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    LoginIn,
    MessageOut,
    PopularPropertyOut,
    PropertyAdminOut,
    SuggestionOut,
    SyncRunOut,
    TranslationOut,
    TranslationUpsert,
)
from app.security.passwords import verify_password
from app.security.rate_limit import login_limiter
from app.security.sessions import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    create_csrf_token,
    create_session_token,
)
from app.services.properties import popular_properties, property_address, property_public_dict
from app.services.sync import run_property_sync

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _set_auth_cookies(response: Response, token: str) -> None:
    settings = get_settings()
    max_age = settings.session_ttl_hours * 3600
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=max_age,
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        create_csrf_token(token),
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=max_age,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


@router.post("/login", response_model=AdminOut)
def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AdminOut:
    settings = get_settings()
    client_ip = get_client_ip(request)
    if not login_limiter.allow(
        f"login:{client_ip}",
        settings.login_rate_limit_per_hour,
        3600,
    ):
        raise HTTPException(status_code=429, detail="Too many login attempts")

    admin = db.scalar(
        select(Administrator).where(
            Administrator.username == payload.username,
            Administrator.is_active.is_(True),
        )
    )
    if admin is None or not verify_password(admin.password_hash, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    admin.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = create_session_token(admin.id, admin.username)
    _set_auth_cookies(response, token)
    return AdminOut(id=admin.id, username=admin.username)


@router.post("/logout", response_model=MessageOut)
def logout(
    response: Response,
    _: Administrator = Depends(get_current_admin),
    __: None = Depends(require_csrf),
) -> MessageOut:
    _clear_auth_cookies(response)
    return MessageOut(message="Logged out")


@router.get("/me", response_model=AdminOut)
def me(admin: Administrator = Depends(get_current_admin)) -> AdminOut:
    return AdminOut(id=admin.id, username=admin.username)


@router.get("/suggestions", response_model=list[SuggestionOut])
def list_suggestions(
    category_id: int | None = None,
    property_id: int | None = None,
    offer_type: str | None = Query(default=None, pattern="^(wynajem|sprzedaz)$"),
    q: str | None = None,
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
) -> list[Suggestion]:
    stmt = (
        select(Suggestion)
        .options(joinedload(Suggestion.category))
        .order_by(Suggestion.created_at.desc())
    )
    if category_id is not None:
        stmt = stmt.where(Suggestion.category_id == category_id)
    if property_id is not None:
        stmt = stmt.where(Suggestion.property_id == property_id)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            Suggestion.proposal_text.ilike(pattern)
            | Suggestion.email.ilike(pattern)
        )
    rows = list(db.scalars(stmt).unique().all())
    if offer_type:
        rows = [
            row
            for row in rows
            if (row.property_snapshot or {}).get("offer_type") == offer_type
        ]
    return rows


@router.get("/suggestions/export")
def export_suggestions(
    category_id: int | None = None,
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
):
    stmt = (
        select(Suggestion)
        .options(joinedload(Suggestion.category))
        .order_by(Suggestion.created_at.desc())
    )
    if category_id is not None:
        stmt = stmt.where(Suggestion.category_id == category_id)
    rows = list(db.scalars(stmt).unique().all())

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "created_at",
            "category",
            "email",
            "proposal_text",
            "property_id",
            "offer_type",
            "address",
            "district",
            "area_m2",
        ]
    )
    for row in rows:
        snapshot = row.property_snapshot or {}
        writer.writerow(
            [
                row.id,
                row.created_at.isoformat() if row.created_at else "",
                row.category.slug if row.category else "",
                row.email or "",
                row.proposal_text.replace("\t", " ").replace("\n", " "),
                row.property_id,
                snapshot.get("offer_type", ""),
                snapshot.get("address_label", ""),
                snapshot.get("district", ""),
                snapshot.get("area_m2", ""),
            ]
        )
    buffer.seek(0)
    filename = f"suggestions-{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/suggestions/{suggestion_id}", response_model=MessageOut)
def delete_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
    __: None = Depends(require_csrf),
) -> MessageOut:
    row = db.get(Suggestion, suggestion_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    db.delete(row)
    db.commit()
    return MessageOut(message="Suggestion deleted")


@router.get("/categories", response_model=list[CategoryOut])
def admin_categories(
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
) -> list[ProposalCategory]:
    return list(
        db.scalars(
            select(ProposalCategory).order_by(
                ProposalCategory.sort_order.asc(), ProposalCategory.id.asc()
            )
        ).all()
    )


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
    __: None = Depends(require_csrf),
) -> ProposalCategory:
    exists = db.scalar(
        select(ProposalCategory).where(ProposalCategory.slug == payload.slug)
    )
    if exists:
        raise HTTPException(status_code=400, detail="Slug already exists")
    row = ProposalCategory(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
    __: None = Depends(require_csrf),
) -> ProposalCategory:
    row = db.get(ProposalCategory, category_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.get("/translations", response_model=list[TranslationOut])
def admin_translations(
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
) -> list[SourceTranslation]:
    return list(
        db.scalars(
            select(SourceTranslation).order_by(
                SourceTranslation.field_name, SourceTranslation.source_value
            )
        ).all()
    )


@router.post("/translations", response_model=TranslationOut)
def upsert_translation(
    payload: TranslationUpsert,
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
    __: None = Depends(require_csrf),
) -> SourceTranslation:
    row = db.scalar(
        select(SourceTranslation).where(
            SourceTranslation.field_name == payload.field_name,
            SourceTranslation.source_value == payload.source_value,
        )
    )
    if row is None:
        row = SourceTranslation(**payload.model_dump())
        db.add(row)
    else:
        row.value_en = payload.value_en
    db.commit()
    db.refresh(row)
    return row


@router.get("/sync", response_model=list[SyncRunOut])
def sync_history(
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
) -> list[SyncRun]:
    return list(
        db.scalars(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(20)).all()
    )


@router.post("/sync", response_model=SyncRunOut)
def trigger_sync(
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
    __: None = Depends(require_csrf),
) -> SyncRun:
    return run_property_sync(db)


@router.get("/popular", response_model=list[PopularPropertyOut])
def popular(
    category_id: int | None = None,
    offer_type: str | None = Query(default=None, pattern="^(wynajem|sprzedaz)$"),
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
) -> list[dict]:
    return popular_properties(db, category_id=category_id, offer_type=offer_type)


@router.get("/properties/{property_id}", response_model=PropertyAdminOut)
def admin_property(
    property_id: int,
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
) -> PropertyAdminOut:
    row = db.get(Property, property_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Property not found")
    data = property_public_dict(row)
    data.update(
        {
            "status": row.status,
            "starting_rate": row.starting_rate,
            "starting_price": row.starting_price,
            "rental_term": row.rental_term,
            "rental_mode": row.rental_mode,
            "announcement_url": row.announcement_url,
            "is_active": row.is_active,
            "synced_at": row.synced_at,
        }
    )
    return PropertyAdminOut(**data)


@router.post("/retention/run", response_model=MessageOut)
def run_retention(
    db: Session = Depends(get_db),
    _: Administrator = Depends(get_current_admin),
    __: None = Depends(require_csrf),
) -> MessageOut:
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days)
    old = list(db.scalars(select(Suggestion).where(Suggestion.created_at < cutoff)).all())
    for row in old:
        db.delete(row)
    db.commit()
    return MessageOut(message=f"Deleted {len(old)} expired suggestions")
