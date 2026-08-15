"""
Automated background scheduler for executing scheduled financial controls.
"""
import os
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.db.session import SessionLocal, init_db
from src.db.models import ControlModel
from src.engine.loader import load_control_from_yaml_str
from src.engine.executor import ControlExecutor
from src.components.registry import ComponentRegistry


def run_scheduled_controls(db: Session, triggered_by: str = "scheduler"):
    """
    Execute all enabled controls that have an active schedule defined.
    """
    controls = db.query(ControlModel).filter(
        ControlModel.enabled == True,
        ControlModel.schedule != None
    ).all()

    registry = ComponentRegistry.default()
    executor = ControlExecutor(registry=registry, db=db)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    results = []
    for ctrl_record in controls:
        try:
            ctrl_def = load_control_from_yaml_str(ctrl_record.config_yaml)
            res = executor.execute_control(
                control=ctrl_def,
                as_of_date=today_str,
                triggered_by=triggered_by,
                db_session=db
            )
            results.append(res)
            print(f"[{datetime.now(timezone.utc).isoformat()}] Executed scheduled control: {ctrl_record.name} -> {res['status']} ({res['breach_count']} breaches)")
        except Exception as e:
            print(f"Error executing scheduled control {ctrl_record.name}: {e}")

    return results


def start_scheduler_loop(interval_seconds: int = 60):
    """
    Continuous polling worker for Docker scheduler container.
    """
    print(f"Control Automation Scheduler worker started. Polling every {interval_seconds}s...")
    init_db()

    while True:
        db = SessionLocal()
        try:
            run_scheduled_controls(db)
        finally:
            db.close()
        time.sleep(interval_seconds)


if __name__ == "__main__":
    poll_sec = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
    start_scheduler_loop(poll_sec)
