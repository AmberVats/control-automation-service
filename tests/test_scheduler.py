import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.models import Base, ControlModel
from src.scheduler.cron import run_scheduled_controls


@pytest.fixture
def mem_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_run_scheduled_controls(mem_db):
    # Insert scheduled control
    yaml_content = """
    name: test_scheduled_recon
    version: 1
    component: tolerance.threshold_check
    parameters:
      expected: 100
      actual: 100
      tolerance: 5
    """
    ctrl = ControlModel(
        name="test_scheduled_recon",
        version="1",
        component="tolerance.threshold_check",
        schedule="0 18 * * 1-5",
        config_yaml=yaml_content,
        config_hash="abc123456",
        enabled=True
    )
    mem_db.add(ctrl)
    mem_db.commit()

    results = run_scheduled_controls(mem_db, triggered_by="test_scheduler")
    assert len(results) == 1
    assert results[0]["status"] == "PASS"
    assert results[0]["triggered_by"] == "test_scheduler"
