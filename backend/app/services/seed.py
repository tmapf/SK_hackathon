from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProposalCategory, SourceTranslation
from app.security.passwords import hash_password
from app.models import Administrator

SEED_CATEGORIES = [
    ("retail", "Sklep / handel", "Retail", 10),
    ("office", "Biuro", "Office", 20),
    ("food", "Gastronomia", "Food and hospitality", 30),
    ("services", "Usługi", "Services", 40),
    ("culture", "Kultura i działalność twórcza", "Culture and creative activity", 50),
    ("community", "Działalność społeczna", "Community or nonprofit use", 60),
    ("warehouse", "Magazyn i logistyka", "Warehouse or logistics", 70),
]

SEED_TRANSLATIONS = [
    ("intended_use", "BIUROWA", "Office"),
    ("intended_use", "HANDLOWA", "Retail"),
    ("intended_use", "USŁUGOWA", "Services"),
    ("intended_use", "MAGAZYN", "Warehouse"),
    ("intended_use", "PRACOWNIA TWÓRCZA", "Creative workshop"),
    ("development_state", "gruntowa niezabudowana", "Undeveloped land"),
    ("development_state", "gruntowa zabudowana", "Developed land"),
    ("development_state", "lokal mieszkalny", "Residential unit"),
]


def seed_defaults(db: Session) -> None:
    for slug, label_pl, label_en, sort_order in SEED_CATEGORIES:
        existing = db.scalar(select(ProposalCategory).where(ProposalCategory.slug == slug))
        if existing is None:
            db.add(
                ProposalCategory(
                    slug=slug,
                    label_pl=label_pl,
                    label_en=label_en,
                    sort_order=sort_order,
                    is_active=True,
                )
            )

    for field_name, source_value, value_en in SEED_TRANSLATIONS:
        existing = db.scalar(
            select(SourceTranslation).where(
                SourceTranslation.field_name == field_name,
                SourceTranslation.source_value == source_value,
            )
        )
        if existing is None:
            db.add(
                SourceTranslation(
                    field_name=field_name,
                    source_value=source_value,
                    value_en=value_en,
                )
            )
    db.commit()


def ensure_admin(db: Session, username: str, password: str) -> Administrator:
    admin = db.scalar(select(Administrator).where(Administrator.username == username))
    if admin is None:
        admin = Administrator(username=username, password_hash=hash_password(password))
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin
