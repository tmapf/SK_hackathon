from app.services.warsaw_client import (
    WarsawPropertyClient,
    build_address_label,
    normalize_property_fields,
)


def test_parse_coordinates_valid():
    assert WarsawPropertyClient.parse_coordinates("21.01,52.22") == (21.01, 52.22)


def test_parse_coordinates_null_string():
    assert WarsawPropertyClient.parse_coordinates("null,null") is None
    assert WarsawPropertyClient.parse_coordinates(None) is None
    assert WarsawPropertyClient.parse_coordinates("") is None


def test_normalize_rental_fields():
    record = {
        "offer_type": "wynajem",
        "source_id": 1,
        "longitude": 21.0,
        "latitude": 52.0,
        "raw": {
            "id": 1,
            "ulica": "Lipska",
            "numerDomu": "21",
            "dzielnica": "Praga-Południe",
            "powierzchnia": 19.76,
            "przeznaczenie": "BIUROWA",
            "ogloszenie": "https://example.com",
        },
        "location": {"lokalizacja": "21.0,52.0", "wspolrzedne": None},
    }
    fields = normalize_property_fields(record)
    assert fields["intended_use"] == "BIUROWA"
    assert fields["development_state"] is None
    assert fields["announcement_url"] == "https://example.com"


def test_address_label():
    label = build_address_label(
        street="ul. Test",
        house_number="1",
        unit_number="2",
        district="Wola",
        city="Warszawa",
    )
    assert label == "ul. Test 1/2, Wola, Warszawa"
