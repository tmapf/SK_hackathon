from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Property, SyncRun
from app.services.warsaw_client import (
    WarsawPropertyClient,
    normalize_property_fields,
)


def run_property_sync(
    db: Session,
    *,
    kinds: tuple[str, ...] = ("wynajem", "sprzedaz"),
    limit: int | None = None,
) -> SyncRun:
    run = SyncRun(
        status="running",
        offer_types=",".join(kinds),
        properties_upserted=0,
        properties_skipped=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    upserted = 0
    skipped = 0
    seen_keys: set[tuple[str, int]] = set()

    try:
        with WarsawPropertyClient() as client:
            for kind in kinds:
                listed = client.list_properties(kind)  # type: ignore[arg-type]
                if limit is not None:
                    listed = listed[:limit]
                for property_data in listed:
                    location = client.get_location(kind, int(property_data["id"]))  # type: ignore[arg-type]
                    coords = client.parse_coordinates(location.get("lokalizacja"))
                    if coords is None:
                        skipped += 1
                        continue
                    longitude, latitude = coords
                    record = {
                        "offer_type": kind,
                        "source_id": int(property_data["id"]),
                        "raw": property_data,
                        "location": location,
                        "longitude": longitude,
                        "latitude": latitude,
                    }
                    fields = normalize_property_fields(record)
                    key = (fields["offer_type"], fields["source_id"])
                    seen_keys.add(key)

                    existing = db.scalar(
                        select(Property).where(
                            Property.offer_type == fields["offer_type"],
                            Property.source_id == fields["source_id"],
                        )
                    )
                    if existing is None:
                        property_row = Property(**fields)
                        db.add(property_row)
                    else:
                        for attr, value in fields.items():
                            setattr(existing, attr, value)
                        existing.synced_at = datetime.now(timezone.utc)
                    upserted += 1

        # Deactivate properties that disappeared from the feed for synced kinds
        for offer_type in kinds:
            rows = db.scalars(
                select(Property).where(Property.offer_type == offer_type)
            ).all()
            for row in rows:
                if (row.offer_type, row.source_id) not in seen_keys:
                    row.is_active = False

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


def latest_successful_sync(db: Session) -> SyncRun | None:
    return db.scalar(
        select(SyncRun)
        .where(SyncRun.status == "success")
        .order_by(SyncRun.finished_at.desc())
        .limit(1)
    )
