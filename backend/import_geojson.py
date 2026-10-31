#!/usr/bin/env python3
"""Import a local Warsaw GeoJSON export into the properties table."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.services.geojson_import import import_geojson_file
from app.services.seed import seed_defaults


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Warsaw properties GeoJSON")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("/data/warsaw_properties.geojson"),
    )
    args = parser.parse_args()
    if not args.path.exists():
        raise SystemExit(f"GeoJSON not found: {args.path}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_defaults(db)
        run = import_geojson_file(db, args.path)
        print(
            f"Import {run.status}: upserted={run.properties_upserted} "
            f"skipped={run.properties_skipped}"
        )
        if run.error_message:
            print(run.error_message)
    finally:
        db.close()


if __name__ == "__main__":
    main()
