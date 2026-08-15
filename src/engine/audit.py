import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from src.db.models import ControlRunModel, ControlExceptionModel


class AuditLogger:
    def __init__(self, db: Session):
        self.db = db

    def log_run(
        self,
        run_id: str,
        control_name: str,
        version: str,
        config_hash: str,
        status: str,
        start_time: datetime,
        end_time: datetime,
        duration_ms: float,
        triggered_by: str = "api",
        as_of_date: Optional[str] = None,
        row_count_in: int = 0,
        row_count_out: int = 0,
        breach_count: int = 0,
        error_message: Optional[str] = None,
        breaches: Optional[List[Dict[str, Any]]] = None
    ) -> ControlRunModel:
        """Persist a complete control run and its associated exceptions to the audit trail."""
        run_record = ControlRunModel(
            run_id=run_id,
            control_name=control_name,
            version=str(version),
            config_hash=config_hash,
            triggered_by=triggered_by,
            as_of_date=as_of_date,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            status=status,
            row_count_in=row_count_in,
            row_count_out=row_count_out,
            breach_count=breach_count,
            error_message=error_message
        )

        self.db.add(run_record)
        self.db.flush()

        if breaches:
            for b in breaches:
                # Extract key information safely
                key_raw = b.get("key") or b.get("foreign_key_value") or b.get("row_index")
                key_str = json.dumps(key_raw) if isinstance(key_raw, (dict, list, tuple)) else str(key_raw) if key_raw is not None else None

                exc = ControlExceptionModel(
                    run_id=run_id,
                    exception_type=b.get("type", "BREACH"),
                    key_data=key_str,
                    field=b.get("field"),
                    source_val=str(b.get("source_value")) if b.get("source_value") is not None else None,
                    target_val=str(b.get("target_value")) if b.get("target_value") is not None else None,
                    difference=float(b.get("difference")) if b.get("difference") is not None else None,
                    message=b.get("message") or b.get("description")
                )
                self.db.add(exc)

        self.db.commit()
        self.db.refresh(run_record)
        return run_record
