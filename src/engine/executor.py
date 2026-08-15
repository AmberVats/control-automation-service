import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.components.registry import ComponentRegistry
from src.engine.schemas import ControlDefinitionSchema, DataSourceConfig
from src.engine.audit import AuditLogger


class ControlExecutor:
    def __init__(self, registry: Optional[ComponentRegistry] = None, db: Optional[Session] = None):
        self.registry = registry or ComponentRegistry.default()
        self.db = db

    def resolve_data_source(
        self,
        source_config: Any,
        db_session: Optional[Session] = None,
        as_of_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Resolve data from inline list, SQL query, or file."""
        if not source_config:
            return []

        if hasattr(source_config, "model_dump"):
            source_config = source_config.model_dump(exclude_none=True)

        if isinstance(source_config, list):
            return source_config

        if isinstance(source_config, dict):
            # 1. Inline data
            if "data" in source_config and source_config["data"] is not None:
                return source_config["data"]

            # 2. Query file
            query_file = source_config.get("query_file")
            if query_file:
                query_path = Path(query_file)
                if not query_path.exists():
                    # check in queries directory
                    query_path = Path("queries") / query_path.name
                if query_path.exists():
                    with open(query_path, "r", encoding="utf-8") as f:
                        sql_query = f.read()
                    if db_session:
                        params = {"as_of_date": as_of_date} if as_of_date else {}
                        try:
                            result = db_session.execute(text(sql_query), params)
                        except Exception:
                            result = db_session.execute(text(sql_query))
                        columns = list(result.keys())
                        return [dict(zip(columns, row)) for row in result.fetchall()]

            # 3. Direct SQL query
            sql_query = source_config.get("query")
            if sql_query and db_session:
                params = {"as_of_date": as_of_date} if as_of_date else {}
                try:
                    result = db_session.execute(text(sql_query), params)
                except Exception:
                    result = db_session.execute(text(sql_query))
                columns = list(result.keys())
                return [dict(zip(columns, row)) for row in result.fetchall()]

        return []

    def execute_control(
        self,
        control: ControlDefinitionSchema,
        runtime_data: Optional[Dict[str, Any]] = None,
        as_of_date: Optional[str] = None,
        triggered_by: str = "api",
        db_session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Execute a control definition and persist the audit trail.
        """
        db = db_session or self.db
        run_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        start_t = time.perf_counter()
        config_hash = control.compute_hash()

        # Build payload for component execution
        payload: Dict[str, Any] = {}
        row_count_in = 0

        try:
            if runtime_data:
                payload = runtime_data.copy()
            else:
                # Resolve data from control specification
                if control.source:
                    src_data = self.resolve_data_source(control.source, db, as_of_date)
                    payload["source"] = src_data
                    payload["data"] = src_data  # For quality components
                    row_count_in += len(src_data)

                if control.target:
                    tgt_data = self.resolve_data_source(control.target, db, as_of_date)
                    payload["target"] = tgt_data
                    row_count_in += len(tgt_data)

                if control.lookup:
                    lookup_data = self.resolve_data_source(control.lookup, db, as_of_date)
                    payload["lookup"] = lookup_data
                    row_count_in += len(lookup_data)

                if control.keys:
                    payload["keys"] = control.keys

                if control.compare:
                    payload["compare"] = control.compare

                if control.tolerance:
                    # Format tolerance dictionary if needed
                    tol_dict = {}
                    for k, v in control.tolerance.items():
                        if hasattr(v, "model_dump"):
                            tol_dict[k] = v.model_dump(exclude_none=True)
                        elif isinstance(v, (int, float)):
                            tol_dict[k] = {"absolute": v}
                        else:
                            tol_dict[k] = v
                    payload["tolerance"] = tol_dict

                if control.parameters:
                    payload.update(control.parameters)

            # Ensure as_of_date is passed if specified
            if as_of_date:
                payload["as_of_date"] = as_of_date

            # Execute component via registry
            component_result = self.registry.execute(control.component, payload)

            end_t = time.perf_counter()
            end_time = datetime.now(timezone.utc)
            duration_ms = round((end_t - start_t) * 1000.0, 2)

            status = component_result.get("status", "PASS")
            breaches = component_result.get("breaches", [])
            breach_count = component_result.get("breach_count", len(breaches))

            run_summary = {
                "run_id": run_id,
                "control_name": control.name,
                "version": str(control.version),
                "config_hash": config_hash,
                "status": status,
                "triggered_by": triggered_by,
                "as_of_date": as_of_date,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_ms": duration_ms,
                "row_count_in": row_count_in,
                "breach_count": breach_count,
                "breaches": breaches,
                "error_message": None
            }

            # Persist to database if session is available
            if db:
                audit = AuditLogger(db)
                audit.log_run(
                    run_id=run_id,
                    control_name=control.name,
                    version=str(control.version),
                    config_hash=config_hash,
                    status=status,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    triggered_by=triggered_by,
                    as_of_date=as_of_date,
                    row_count_in=row_count_in,
                    row_count_out=row_count_in - breach_count,
                    breach_count=breach_count,
                    breaches=breaches
                )

            return run_summary

        except Exception as e:
            end_t = time.perf_counter()
            end_time = datetime.now(timezone.utc)
            duration_ms = round((end_t - start_t) * 1000.0, 2)

            error_summary = {
                "run_id": run_id,
                "control_name": control.name,
                "version": str(control.version),
                "config_hash": config_hash,
                "status": "FAIL",
                "triggered_by": triggered_by,
                "as_of_date": as_of_date,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_ms": duration_ms,
                "row_count_in": row_count_in,
                "breach_count": 0,
                "breaches": [],
                "error_message": str(e)
            }

            if db:
                audit = AuditLogger(db)
                audit.log_run(
                    run_id=run_id,
                    control_name=control.name,
                    version=str(control.version),
                    config_hash=config_hash,
                    status="FAIL",
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    triggered_by=triggered_by,
                    as_of_date=as_of_date,
                    row_count_in=row_count_in,
                    breach_count=0,
                    error_message=str(e),
                    breaches=[]
                )

            return error_summary
