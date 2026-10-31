from app.models import Property


def test_address_suggestions(client, db_session):
    db_session.add(
        Property(
            offer_type="wynajem",
            source_id=901,
            street="Lipska",
            district="Praga-Południe",
            city="Warszawa",
            house_number="21",
            area_m2=20.0,
            intended_use="BIUROWA",
            longitude=21.05,
            latitude=52.23,
            is_active=True,
            raw_payload={},
        )
    )
    db_session.commit()

    response = client.get("/api/address-suggestions?q=Lips&offer_type=wynajem")
    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["street"] == "Lipska"
    assert "Praga-Południe" in payload[0]["address_label"]
