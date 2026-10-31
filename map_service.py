"""CLI wrapper around the Warsaw municipal property connector.

The reusable client lives in ``backend.app.services.warsaw_client``.
This script remains a convenient offline GeoJSON exporter.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services.warsaw_client import (  # noqa: E402
    WarsawPropertyClient,
    normalize_property_fields,
)
from app.services.warsaw_client import build_address_label  # noqa: E402


def build_geojson(kinds: tuple[str, ...], limit: int | None = None) -> dict:
    features = []
    with WarsawPropertyClient() as client:
        for kind in kinds:
            for record in client.iter_mappable_properties(kind, limit=limit):  # type: ignore[arg-type]
                fields = normalize_property_fields(record)
                features.append(
                    {
                        "type": "Feature",
                        "id": fields["source_id"],
                        "geometry": {
                            "type": "Point",
                            "coordinates": [fields["longitude"], fields["latitude"]],
                        },
                        "properties": {
                            **fields,
                            "address_label": build_address_label(
                                street=fields["street"],
                                house_number=fields["house_number"],
                                unit_number=fields["unit_number"],
                                district=fields["district"],
                                city=fields["city"],
                            ),
                            "offerType": fields["offer_type"],
                        },
                    }
                )
    return {
        "type": "FeatureCollection",
        "name": "Warsaw municipal properties",
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download points from the Warsaw municipal property map."
    )
    parser.add_argument(
        "--kind",
        choices=("sprzedaz", "wynajem", "all"),
        default="all",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("warsaw_properties.geojson"),
    )
    args = parser.parse_args()
    kinds = ("sprzedaz", "wynajem") if args.kind == "all" else (args.kind,)
    geojson = build_geojson(kinds, limit=args.limit)
    args.output.write_text(
        json.dumps(geojson, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {len(geojson['features'])} points to {args.output}")


if __name__ == "__main__":
    main()
