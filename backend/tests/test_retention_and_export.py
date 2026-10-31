from datetime import datetime, timedelta, timezone

from app.models import ProposalCategory, Property, Suggestion


def _add_property(db_session, source_id: int = 501) -> Property:
    row = Property(
        offer_type="wynajem",
        source_id=source_id,
        street="Testowa",
        district="Wola",
        city="Warszawa",
        area_m2=40.0,
        intended_use="BIUROWA",
        longitude=21.0,
        latitude=52.2,
        is_active=True,
        announcement_url="https://example.com/offer",
        raw_payload={},
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


def test_csv_export_and_retention(client, db_session):
    property_row = _add_property(db_session)
    category = db_session.query(ProposalCategory).first()
    old = Suggestion(
        property_id=property_row.id,
        category_id=category.id,
        proposal_text="Old proposal that should be removed by retention.",
        email="old@example.com",
        property_snapshot={
            "offer_type": "wynajem",
            "address_label": "Testowa, Wola",
            "district": "Wola",
            "area_m2": 40.0,
            "announcement_url": "https://example.com/offer",
        },
        created_at=datetime.now(timezone.utc) - timedelta(days=400),
    )
    fresh = Suggestion(
        property_id=property_row.id,
        category_id=category.id,
        proposal_text="Fresh proposal that should remain after retention.",
        email="fresh@example.com",
        property_snapshot={
            "offer_type": "wynajem",
            "address_label": "Testowa, Wola",
            "district": "Wola",
            "area_m2": 40.0,
        },
    )
    db_session.add_all([old, fresh])
    db_session.commit()

    login = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "adminpass123"},
    )
    assert login.status_code == 200

    export = client.get("/api/admin/suggestions/export")
    assert export.status_code == 200
    assert "text/csv" in export.headers["content-type"]
    assert "Fresh proposal" in export.text
    assert "old@example.com" in export.text

    retention = client.post("/api/admin/retention/run")
    assert retention.status_code == 200
    assert "Deleted 1" in retention.json()["message"]

    listed = client.get("/api/admin/suggestions")
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["email"] == "fresh@example.com"
