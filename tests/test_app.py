from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select
from app.models.entities import Order
from app.services.phone import is_valid_algerian_phone, normalize_algerian_phone
from scripts.seed_demo import seed_session


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_local_cors_preflight(client):
    response = client.options(
        "/api/orders",
        headers={
            "Origin": "http://127.0.0.1:8000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8000"


def test_phone_normalization():
    assert normalize_algerian_phone("0551 00 00 01") == "+213551000001"
    assert normalize_algerian_phone("213662000003") == "+213662000003"
    assert normalize_algerian_phone("+213 773 000 004") == "+213773000004"
    assert normalize_algerian_phone("00213 662 000 003") == "+213662000003"
    assert is_valid_algerian_phone("0773-000-004")
    assert not is_valid_algerian_phone("123")


def test_landing_dashboard_and_evaluate_pages(client):
    assert client.get("/").status_code == 200
    assert client.get("/dashboard").status_code == 200
    assert client.get("/evaluate").status_code == 200


def test_create_order_and_risk(client):
    response = client.post("/api/orders", json={
        "phone": "0551000001", "wilaya": "Alger", "amount_dzd": 4500,
        "product_category": "Vetements", "order_channel": "Facebook",
        "is_confirmed": True, "contact_attempts": 1
    })
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] >= 70
    assert data["risk_level"] == "low"


def test_risk_scoring_high(client):
    response = client.post("/api/risk/evaluate", json={
        "phone": "123", "wilaya": "Oran", "amount_dzd": 40000,
        "product_category": "Electronique", "order_channel": "Instagram",
        "is_confirmed": False, "contact_attempts": 4
    })
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "high"
    assert any("الهاتف" in reason for reason in data["reasons"])


def test_invalid_phone_order_is_scored_not_rejected(client):
    response = client.post("/api/orders", json={
        "phone": "123", "wilaya": "Oran", "amount_dzd": 40000,
        "product_category": "Electronique", "order_channel": "Instagram",
        "is_confirmed": False, "contact_attempts": 4
    })
    assert response.status_code == 200
    assert response.json()["risk_level"] == "high"


def test_status_customer_dashboard(client):
    order = client.post("/api/orders", json={
        "phone": "0662000003", "wilaya": "Setif", "amount_dzd": 12000,
        "product_category": "Maison", "order_channel": "WhatsApp",
        "is_confirmed": True, "contact_attempts": 1
    }).json()
    updated = client.patch(f"/api/orders/{order['id']}/status", json={"status": "Delivered"})
    assert updated.status_code == 200
    stats = client.get("/api/customers/0662000003").json()
    assert stats["delivered"] == 1
    assert stats["success_rate"] == 100
    summary = client.get("/api/dashboard/summary").json()
    assert summary["total_orders"] >= 1
    assert summary["delivered"] == 1


def test_demo_seed_is_idempotent():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        assert seed_session(session) == 28
        assert seed_session(session) == 0
        assert len(session.exec(select(Order)).all()) == 28
