import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.db.models import Base
from src.db.session import get_db

# Create isolated test database with StaticPool so all connections share the same memory database
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_components_catalogue():
    response = client.get("/api/v1/components")
    assert response.status_code == 200
    components = response.json()
    assert len(components) >= 5
    comp_names = [c["name"] for c in components]
    assert "reconciliation.two_way_match" in comp_names
    assert "tolerance.threshold_check" in comp_names
    assert "quality.completeness" in comp_names
    assert "quality.referential_integrity" in comp_names
    assert "quality.staleness" in comp_names


def test_control_registration_and_execution_flow():
    # 1. Register a control via YAML
    yaml_payload = """
    name: test_recon_control
    version: 1
    component: reconciliation.two_way_match
    description: Test two-way match for positions
    keys: [instrument_id]
    compare: [quantity]
    tolerance:
      quantity: { absolute: 0 }
    """
    reg_resp = client.post("/api/v1/controls", json={"yaml_content": yaml_payload})
    assert reg_resp.status_code == 201
    control_data = reg_resp.json()
    assert control_data["name"] == "test_recon_control"
    assert control_data["component"] == "reconciliation.two_way_match"

    # 2. List controls
    list_resp = client.get("/api/v1/controls")
    assert list_resp.status_code == 200
    assert any(c["name"] == "test_recon_control" for c in list_resp.json())

    # 3. Get control detail
    detail_resp = client.get("/api/v1/controls/test_recon_control")
    assert detail_resp.status_code == 200
    assert "test_recon_control" in detail_resp.json()["config_yaml"]

    # 4. Run control with payload containing a mismatch
    run_req = {
        "as_of_date": "2026-08-15",
        "triggered_by": "api_test",
        "data": {
            "source": [{"instrument_id": "BOND_1", "quantity": 1000}],
            "target": [{"instrument_id": "BOND_1", "quantity": 950}],
            "keys": ["instrument_id"],
            "compare": ["quantity"],
            "tolerance": {"quantity": {"absolute": 0}}
        }
    }
    run_resp = client.post("/api/v1/controls/test_recon_control/run", json=run_req)
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "BREACH"
    assert run_data["breach_count"] == 1
    run_id = run_data["run_id"]

    # 5. Get run details
    run_detail_resp = client.get(f"/api/v1/runs/{run_id}")
    assert run_detail_resp.status_code == 200
    assert run_detail_resp.json()["status"] == "BREACH"

    # 6. Get run exceptions
    exc_resp = client.get(f"/api/v1/runs/{run_id}/exceptions")
    assert exc_resp.status_code == 200
    exc_data = exc_resp.json()
    assert exc_data["total_breaches"] == 1
    assert exc_data["exceptions"][0]["field"] == "quantity"
    assert exc_data["exceptions"][0]["difference"] == 50.0

    # 7. List historical runs
    runs_list_resp = client.get("/api/v1/runs")
    assert runs_list_resp.status_code == 200
    assert len(runs_list_resp.json()) >= 1


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["status"] == "operational"
    assert metrics["total_registered_controls"] >= 1
    assert metrics["total_runs_executed"] >= 1
