"""HTTP client for the Warsaw municipal property map API."""

from __future__ import annotations

import math
from typing import Any, Iterator, Literal

import httpx

BASE_URL = "https://mapa.um.warszawa.pl/api/modul-mapowy/open/nieruchomosci"
PropertyKind = Literal["sprzedaz", "wynajem"]


class WarsawPropertyClient:
    """Client for the public API used by mapa.um.warszawa.pl."""

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "WarsawPropertyIdeas/1.0",
            },
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> WarsawPropertyClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _get(self, path: str, **params: Any) -> Any:
        response = self._client.get(
            f"{BASE_URL}/{path}",
            params={key: value for key, value in params.items() if value is not None},
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("content", payload)

    def list_properties(
        self, kind: PropertyKind, **filters: Any
    ) -> list[dict[str, Any]]:
        content = self._get(kind, **filters)
        if not isinstance(content, list):
            raise ValueError(f"Unexpected list response for {kind!r}")
        return content

    def get_location(self, kind: PropertyKind, property_id: int) -> dict[str, Any]:
        content = self._get(f"{kind}/lokalizacja", id=property_id)
        if not isinstance(content, dict):
            raise ValueError(f"Unexpected location response for property {property_id}")
        return content

    @staticmethod
    def parse_coordinates(coordinate_text: Any) -> tuple[float, float] | None:
        if not coordinate_text or not isinstance(coordinate_text, str):
            return None
        parts = coordinate_text.split(",")
        if len(parts) != 2:
            return None
        if any(value.strip().lower() in {"", "null", "none"} for value in parts):
            return None
        try:
            longitude, latitude = (float(value.strip()) for value in parts)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(longitude) or not math.isfinite(latitude):
            return None
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            return None
        return longitude, latitude

    def iter_mappable_properties(
        self,
        kind: PropertyKind,
        *,
        limit: int | None = None,
        **filters: Any,
    ) -> Iterator[dict[str, Any]]:
        properties = self.list_properties(kind, **filters)
        if limit is not None:
            properties = properties[:limit]

        for property_data in properties:
            location = self.get_location(kind, int(property_data["id"]))
            coords = self.parse_coordinates(location.get("lokalizacja"))
            if coords is None:
                continue
            longitude, latitude = coords
            yield {
                "offer_type": kind,
                "source_id": int(property_data["id"]),
                "raw": property_data,
                "location": location,
                "longitude": longitude,
                "latitude": latitude,
            }


def normalize_property_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Map verified Warsaw API fields into the local property schema."""
    raw = record["raw"]
    offer_type = record["offer_type"]

    street = raw.get("ulica")
    house_number = raw.get("numerDomu")
    unit_number = raw.get("numerLokalu")

    return {
        "offer_type": offer_type,
        "source_id": record["source_id"],
        "street": street,
        "district": raw.get("dzielnica"),
        "city": raw.get("miejscowosc"),
        "house_number": house_number,
        "unit_number": unit_number,
        "area_m2": _as_float(raw.get("powierzchnia")),
        "intended_use": raw.get("przeznaczenie") if offer_type == "wynajem" else None,
        "development_state": (
            raw.get("stanZagospodarowania") if offer_type == "sprzedaz" else None
        ),
        "status": raw.get("status"),
        "starting_rate": _as_float(raw.get("stawkaWywolawcza")),
        "starting_price": _as_float(raw.get("cenaWywolawcza")),
        "rental_term": str(raw.get("okresNajmu")) if raw.get("okresNajmu") is not None else None,
        "rental_mode": raw.get("trybNajmu"),
        "announcement_url": raw.get("ogloszenie"),
        "longitude": record["longitude"],
        "latitude": record["latitude"],
        "raw_payload": {
            "listing": raw,
            "location": {
                "lokalizacja": record["location"].get("lokalizacja"),
                "wspolrzedne": record["location"].get("wspolrzedne"),
            },
        },
        "is_active": True,
    }


def build_address_label(
    *,
    street: str | None,
    house_number: str | None,
    unit_number: str | None,
    district: str | None,
    city: str | None,
) -> str:
    parts: list[str] = []
    if street:
        street_part = street
        if house_number:
            street_part = f"{street_part} {house_number}"
        if unit_number:
            street_part = f"{street_part}/{unit_number}"
        parts.append(street_part)
    if district:
        parts.append(district)
    if city and city not in parts:
        parts.append(city)
    return ", ".join(parts) if parts else "Warsaw property"


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
