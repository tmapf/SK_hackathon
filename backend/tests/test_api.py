from app.models import Property, ProposalCategory


def _add_property(db_session, **overrides):
    data = {
        "offer_type": "wynajem",
        "source_id": 101,
        "street": "Lipska",
        "district": "Praga-Południe",
        "city": "Warszawa",
        "house_number": "21",
        "area_m2": 20.0,
        "intended_use": "BIUROWA",
        "longitude": 21.05,
        "latitude": 52.23,
        "is_active": True,
        "raw_payload": {},
    }
    data.update(overrides)
    row = Property(**data)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_properties_geojson_hides_announcement(client, db_session):
    _add_property(db_session, announcement_url="https://secret.example")
    response = client.get("/api/properties?offer_type=wynajem")
    assert response.status_code == 200
    payload = response.json()
    assert payload["features"]
    props = payload["features"][0]["properties"]
    assert "announcement_url" not in props
    assert props["address_label"]


def test_suggestion_flow(client, db_session):
    property_row = _add_property(db_session)
    category = db_session.query(ProposalCategory).first()
    response = client.post(
        "/api/suggestions",
        json={
            "property_id": property_row.id,
            "category_id": category.id,
            "proposal_text": "Open a neighborhood bakery here.",
            "email": "person@example.com",
            "turnstile_token": "test",
            "website": "",
        },
    )
    assert response.status_code == 201

    login = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "adminpass123"},
    )
    assert login.status_code == 200

    listed = client.get("/api/admin/suggestions")
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["email"] == "person@example.com"


def test_honeypot_rejected(client, db_session):
    property_row = _add_property(db_session, source_id=202)
    category = db_session.query(ProposalCategory).first()
    response = client.post(
        "/api/suggestions",
        json={
            "property_id": property_row.id,
            "category_id": category.id,
            "proposal_text": "Open a neighborhood bakery here.",
            "turnstile_token": "test",
            "website": "http://spam.test",
        },
    )
    assert response.status_code == 400


def test_admin_requires_auth(client):
    response = client.get("/api/admin/suggestions")
    assert response.status_code == 401
