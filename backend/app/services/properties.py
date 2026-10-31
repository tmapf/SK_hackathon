from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Property, SourceTranslation, Suggestion
from app.services.warsaw_client import build_address_label


def property_address(property_row: Property) -> str:
    return build_address_label(
        street=property_row.street,
        house_number=property_row.house_number,
        unit_number=property_row.unit_number,
        district=property_row.district,
        city=property_row.city,
    )


def property_public_dict(property_row: Property) -> dict:
    return {
        "id": property_row.id,
        "offer_type": property_row.offer_type,
        "source_id": property_row.source_id,
        "street": property_row.street,
        "district": property_row.district,
        "city": property_row.city,
        "house_number": property_row.house_number,
        "unit_number": property_row.unit_number,
        "area_m2": property_row.area_m2,
        "intended_use": property_row.intended_use,
        "development_state": property_row.development_state,
        "longitude": property_row.longitude,
        "latitude": property_row.latitude,
        "address_label": property_address(property_row),
    }


def property_snapshot(property_row: Property) -> dict:
    data = property_public_dict(property_row)
    data["announcement_url"] = property_row.announcement_url
    data["status"] = property_row.status
    return data


def filtered_properties_query(
    *,
    offer_type: str | None = None,
    district: str | None = None,
    q: str | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    active_only: bool = True,
) -> Select[tuple[Property]]:
    stmt = select(Property)
    if active_only:
        stmt = stmt.where(Property.is_active.is_(True))
    if offer_type:
        stmt = stmt.where(Property.offer_type == offer_type)
    if district:
        stmt = stmt.where(Property.district == district)
    if min_area is not None:
        stmt = stmt.where(Property.area_m2 >= min_area)
    if max_area is not None:
        stmt = stmt.where(Property.area_m2 <= max_area)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            func.coalesce(Property.street, "").ilike(pattern)
            | func.coalesce(Property.district, "").ilike(pattern)
            | func.coalesce(Property.city, "").ilike(pattern)
            | func.coalesce(Property.house_number, "").ilike(pattern)
        )
    return stmt.order_by(Property.district.asc().nulls_last(), Property.street.asc().nulls_last())


def properties_to_geojson(rows: list[Property]) -> dict:
    features = []
    for row in rows:
        props = property_public_dict(row)
        features.append(
            {
                "type": "Feature",
                "id": row.id,
                "geometry": {
                    "type": "Point",
                    "coordinates": [row.longitude, row.latitude],
                },
                "properties": props,
            }
        )
    return {
        "type": "FeatureCollection",
        "name": "Warsaw municipal properties",
        "features": features,
    }


def list_districts(db: Session, offer_type: str | None = None) -> list[str]:
    stmt = (
        select(Property.district)
        .where(Property.is_active.is_(True), Property.district.is_not(None))
        .distinct()
        .order_by(Property.district.asc())
    )
    if offer_type:
        stmt = stmt.where(Property.offer_type == offer_type)
    return [value for value in db.scalars(stmt).all() if value]


def list_address_suggestions(
    db: Session,
    *,
    q: str,
    offer_type: str | None = None,
    limit: int = 8,
) -> list[dict]:
    query = q.strip()
    if len(query) < 2:
        return []

    stmt = filtered_properties_query(offer_type=offer_type, q=query).limit(limit * 3)
    rows = list(db.scalars(stmt).all())
    suggestions: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        label = property_address(row)
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(
            {
                "id": row.id,
                "address_label": label,
                "district": row.district,
                "street": row.street,
            }
        )
        if len(suggestions) >= limit:
            break
    return suggestions


def translation_map(db: Session) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in db.scalars(select(SourceTranslation)).all():
        result.setdefault(row.field_name, {})[row.source_value] = row.value_en
    return result


def popular_properties(
    db: Session,
    *,
    category_id: int | None = None,
    offer_type: str | None = None,
    limit: int = 100,
) -> list[dict]:
    stmt = (
        select(
            Property,
            func.count(Suggestion.id).label("suggestion_count"),
        )
        .join(Suggestion, Suggestion.property_id == Property.id)
        .group_by(Property.id)
        .order_by(func.count(Suggestion.id).desc())
        .limit(limit)
    )
    if category_id is not None:
        stmt = stmt.where(Suggestion.category_id == category_id)
    if offer_type:
        stmt = stmt.where(Property.offer_type == offer_type)

    rows = db.execute(stmt).all()
    output = []
    for property_row, count in rows:
        output.append(
            {
                "property_id": property_row.id,
                "offer_type": property_row.offer_type,
                "address_label": property_address(property_row),
                "district": property_row.district,
                "area_m2": property_row.area_m2,
                "intended_use": property_row.intended_use,
                "development_state": property_row.development_state,
                "longitude": property_row.longitude,
                "latitude": property_row.latitude,
                "suggestion_count": int(count),
                "announcement_url": property_row.announcement_url,
            }
        )
    return output
