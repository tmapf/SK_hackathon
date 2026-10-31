from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Property, SyncRun
from app.services.warsaw_client import build_address_label, normalize_property_fields


def import_geojson_file(db: Session, path: Path) -> SyncRun:
    """Bootstrap properties from a local GeoJSON export."""
    run = SyncRun(
        status="running",
        offer_types="geojson-import",
        properties_upserted=0,
        properties_skipped=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    upserted = 0
    skipped = 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        features = payload.get("features") or []
        for feature in features:
            try:
                fields = _feature_to_fields(feature)
            except ValueError:
                skipped += 1
                continue

            existing = db.scalar(
                select(Property).where(
                    Property.offer_type == fields["offer_type"],
                    Property.source_id == fields["source_id"],
                )
            )
            if existing is None:
                db.add(Property(**fields))
            else:
                for attr, value in fields.items():
                    setattr(existing, attr, value)
                existing.synced_at = datetime.now(timezone.utc)
            upserted += 1

        run.status = "success"
        run.properties_upserted = upserted
        run.properties_skipped = skipped
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        run = db.get(SyncRun, run.id) or run
        run.status = "failed"
        run.properties_upserted = upserted
        run.properties_skipped = skipped
        run.error_message = str(exc)[:4000]
        run.finished_at = datetime.now(timezone.utc)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run


def _feature_to_fields(feature: dict[str, Any]) -> dict[str, Any]:
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates") or []
    if len(coords) < 2:
        raise ValueError("missing coordinates")
    longitude, latitude = float(coords[0]), float(coords[1])

    props = feature.get("properties") or {}
    offer_type = props.get("offer_type") or props.get("offerType")
    source_id = props.get("source_id") or props.get("id") or feature.get("id")
    if offer_type not in {"wynajem", "sprzedaz"} or source_id is None:
        raise ValueError("missing identity")

    # Prefer already-normalized export fields when present.
    if "street" in props or "district" in props:
        return {
            "offer_type": offer_type,
            "source_id": int(source_id),
            "street": props.get("street") or props.get("ulica"),
            "district": props.get("district") or props.get("dzielnica"),
            "city": props.get("city") or props.get("miejscowosc"),
            "house_number": props.get("house_number") or props.get("numerDomu"),
            "unit_number": props.get("unit_number") or props.get("numerLokalu"),
            "area_m2": _as_float(props.get("area_m2", props.get("powierzchnia"))),
            "intended_use": props.get("intended_use") or props.get("przeznaczenie"),
            "development_state": props.get("development_state")
            or props.get("stanZagospodarowania"),
            "status": props.get("status"),
            "starting_rate": _as_float(
                props.get("starting_rate", props.get("stawkaWywolawcza"))
            ),
            "starting_price": _as_float(
                props.get("starting_price", props.get("cenaWywolawcza"))
            ),
            "rental_term": (
                str(props.get("rental_term") or props.get("okresNajmu"))
                if (props.get("rental_term") or props.get("okresNajmu")) is not None
                else None
            ),
            "rental_mode": props.get("rental_mode") or props.get("trybNajmu"),
            "announcement_url": props.get("announcement_url") or props.get("ogloszenie"),
            "longitude": longitude,
            "latitude": latitude,
            "raw_payload": {"geojson": props},
            "is_active": True,
        }

    record = {
        "offer_type": offer_type,
        "source_id": int(source_id),
        "raw": props,
        "location": {"lokalizacja": f"{longitude},{latitude}"},
        "longitude": longitude,
        "latitude": latitude,
    }
    fields = normalize_property_fields(record)
    # Keep a readable label available in raw payload for debugging.
    fields["raw_payload"] = {
        **(fields.get("raw_payload") or {}),
        "address_label": build_address_label(
            street=fields.get("street"),
            house_number=fields.get("house_number"),
            unit_number=fields.get("unit_number"),
            district=fields.get("district"),
            city=fields.get("city"),
        ),
    }
    return fields


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
