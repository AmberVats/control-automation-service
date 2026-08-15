import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.models import Base, ControlRunModel, ControlExceptionModel
from src.report.html_report import render_html_report, generate_html_report_file
from fastapi.testclient import TestClient
from src.main import app
from src.db.session import get_db
from sqlalchemy.pool import StaticPool

# Setup test DB
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def test_render_html_report_direct():
    run_record = ControlRunModel(
        run_id="test-run-12345678",
        control_name="eod_position_break",
        version="2",
        config_hash="abc1234567890def",
        triggered_by="pytest",
        as_of_date="2026-08-15",
        start_time=datetime.now(timezone.utc),
        duration_ms=45.2,
        status="BREACH",
        row_count_in=100,
        breach_count=1,
    )
    exceptions = [
        ControlExceptionModel(
            run_id="test-run-12345678",
            exception_type="VALUE_MISMATCH",
            key_data='["2026-08-15", "EQ_MSFT", "GLOBAL_EQ"]',
            field="market_value",
            source_val="960120.00",
            target_val="960000.00",
            difference=120.00,
            message="Market value variance exceeds tolerance"
        )
    ]

    html = render_html_report(run_record, exceptions)
    assert "<!DOCTYPE html>" in html
    assert "Global Markets Product Control Analytics" in html
    assert "eod_position_break" in html
    assert "BREACH" in html
    assert "EQ_MSFT" in html
    assert "120.00" in html


def test_get_html_report_endpoint():
    db = TestingSessionLocal()
    run_record = ControlRunModel(
        run_id="html-test-run-999",
        control_name="market_feed_staleness",
        version="1",
        config_hash="fedcba987654321",
        triggered_by="api",
        as_of_date="2026-08-15",
        start_time=datetime.now(timezone.utc),
        duration_ms=15.0,
        status="PASS",
        row_count_in=50,
        breach_count=0,
    )
    db.add(run_record)
    db.commit()
    db.close()

    resp = client.get("/api/v1/runs/html-test-run-999/report.html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "market_feed_staleness" in resp.text
    assert "PASS" in resp.text
