import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.db.models import Base, ControlModel, ControlRunModel, ControlExceptionModel
from src.engine.loader import load_control_from_yaml_str
from src.engine.executor import ControlExecutor
from src.components.registry import ComponentRegistry


@pytest.fixture
def db_session():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    
    # Create views
    with open("sql/02_views.sql", "r", encoding="utf-8") as f:
        views_sql = f.read()
    with test_engine.connect() as conn:
        for stmt in views_sql.split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
        conn.commit()

    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


def test_control_run_and_audit_logging_breach(db_session):
    registry = ComponentRegistry.default()
    executor = ControlExecutor(registry=registry, db=db_session)

    control_yaml = """
    name: eod_position_break
    version: 1
    component: reconciliation.two_way_match
    keys: [instrument_id, book]
    compare: [quantity, market_value]
    tolerance:
      quantity: { absolute: 0 }
      market_value: { absolute: 10 }
    """
    control = load_control_from_yaml_str(control_yaml)

    runtime_data = {
        "source": [
            {"instrument_id": "AAPL", "book": "EQ_DESK", "quantity": 100, "market_value": 15000},
            {"instrument_id": "MSFT", "book": "EQ_DESK", "quantity": 50, "market_value": 15000},
        ],
        "target": [
            {"instrument_id": "AAPL", "book": "EQ_DESK", "quantity": 100, "market_value": 15005},  # within tol
            {"instrument_id": "MSFT", "book": "EQ_DESK", "quantity": 50, "market_value": 15050},  # breach diff=50 > 10
        ],
        "keys": ["instrument_id", "book"],
        "compare": ["quantity", "market_value"],
        "tolerance": {
            "quantity": {"absolute": 0},
            "market_value": {"absolute": 10}
        }
    }

    result = executor.execute_control(
        control=control,
        runtime_data=runtime_data,
        as_of_date="2026-08-15",
        triggered_by="test_suite",
        db_session=db_session
    )

    assert result["status"] == "BREACH"
    assert result["breach_count"] == 1
    assert result["control_name"] == "eod_position_break"

    # Verify database persistence
    run_record = db_session.query(ControlRunModel).filter_by(run_id=result["run_id"]).first()
    assert run_record is not None
    assert run_record.status == "BREACH"
    assert run_record.breach_count == 1
    assert run_record.triggered_by == "test_suite"

    # Verify exception records
    exceptions = db_session.query(ControlExceptionModel).filter_by(run_id=result["run_id"]).all()
    assert len(exceptions) == 1
    assert exceptions[0].field == "market_value"
    assert exceptions[0].difference == 50.0

    # Query view v_control_run_history
    history = db_session.execute(text("SELECT * FROM v_control_run_history WHERE run_id = :rid"), {"rid": result["run_id"]}).fetchall()
    assert len(history) == 1

    # Query view v_recent_exceptions
    recent_exc = db_session.execute(text("SELECT * FROM v_recent_exceptions WHERE run_id = :rid"), {"rid": result["run_id"]}).fetchall()
    assert len(recent_exc) == 1


def test_control_run_pass_and_summary_view(db_session):
    registry = ComponentRegistry.default()
    executor = ControlExecutor(registry=registry, db=db_session)

    control_yaml = """
    name: threshold_check_rates
    version: 1
    component: tolerance.threshold_check
    """
    control = load_control_from_yaml_str(control_yaml)

    runtime_data = {
        "expected": 100.0,
        "actual": 100.2,
        "tolerance": 0.5
    }

    result = executor.execute_control(
        control=control,
        runtime_data=runtime_data,
        as_of_date="2026-08-15",
        triggered_by="api",
        db_session=db_session
    )

    assert result["status"] == "PASS"
    assert result["breach_count"] == 0

    # Check v_control_summary view
    summary = db_session.execute(text("SELECT * FROM v_control_summary WHERE control_name = :cname"), {"cname": "threshold_check_rates"}).fetchall()
    assert len(summary) == 1
    assert summary[0][1] == 1  # total_runs = 1
    assert summary[0][2] == 1  # pass_count = 1
