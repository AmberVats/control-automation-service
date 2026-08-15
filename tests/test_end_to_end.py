import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.db.session import init_db
from src.engine.loader import load_control_from_file
from src.engine.executor import ControlExecutor
from src.components.registry import ComponentRegistry
from data.seed_demo_data import seed_demo_data


@pytest.fixture(scope="module")
def seeded_db():
    db_url = "sqlite:///./data/test_e2e.db"
    seed_demo_data(db_url)
    engine = create_engine(db_url)
    
    # Initialize views
    with open("sql/02_views.sql", "r", encoding="utf-8") as f:
        views_sql = f.read()
    with engine.connect() as conn:
        for stmt in views_sql.split(";"):
            if stmt.strip():
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass
        conn.commit()

    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_e2e_position_reconciliation(seeded_db):
    control = load_control_from_file("controls/eod_position_break.yaml")
    executor = ControlExecutor(db=seeded_db)

    result = executor.execute_control(control, db_session=seeded_db, as_of_date="2026-08-15")

    assert result["status"] == "BREACH"
    assert result["control_name"] == "eod_position_break"
    assert result["breach_count"] >= 1

    # Check that MSFT variance or GOOG missing break was captured
    breach_types = [b["type"] for b in result["breaches"]]
    assert "VALUE_MISMATCH" in breach_types or "MISSING_TARGET" in breach_types


def test_e2e_referential_integrity(seeded_db):
    control = load_control_from_file("controls/trade_referential_integrity.yaml")
    executor = ControlExecutor(db=seeded_db)

    result = executor.execute_control(control, db_session=seeded_db, as_of_date="2026-08-15")

    assert result["status"] == "BREACH"
    assert result["breach_count"] == 1
    assert result["breaches"][0]["foreign_key_value"] == "EQ_INVALID_XYZ"


def test_e2e_feed_staleness(seeded_db):
    control = load_control_from_file("controls/market_feed_staleness.yaml")
    executor = ControlExecutor(db=seeded_db)

    result = executor.execute_control(control, db_session=seeded_db, as_of_date="2026-08-15")

    assert result["status"] == "BREACH"
    assert any(b["type"] == "STALE_DATA" for b in result["breaches"])
