from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.models import ControlModel, ControlRunModel, ControlExceptionModel
from src.engine.loader import load_control_from_yaml_str
from src.engine.executor import ControlExecutor
from src.components.registry import ComponentRegistry
from src.api.schemas import (
    ControlRunRequest,
    RunSummaryResponse,
    PaginatedExceptionsResponse,
    ExceptionItem,
)

router = APIRouter(tags=["Execution & Runs"])


@router.post("/controls/{name}/run", response_model=RunSummaryResponse)
def execute_control_by_name(
    name: str,
    request: Optional[ControlRunRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Execute a registered financial control by name.
    Supports in-flight data overrides or data source resolution.
    """
    control_record = db.query(ControlModel).filter(ControlModel.name == name).first()
    if not control_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control '{name}' not found"
        )

    if not control_record.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Control '{name}' is disabled"
        )

    try:
        control_def = load_control_from_yaml_str(control_record.config_yaml)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing stored control configuration: {str(e)}"
        )

    req = request or ControlRunRequest()
    registry = ComponentRegistry.default()
    executor = ControlExecutor(registry=registry, db=db)

    result = executor.execute_control(
        control=control_def,
        runtime_data=req.data,
        as_of_date=req.as_of_date,
        triggered_by=req.triggered_by or "api",
        db_session=db
    )

    # Fetch stored run from db
    run_record = db.query(ControlRunModel).filter(ControlRunModel.run_id == result["run_id"]).first()
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Execution failed to create audit log"
        )

    return run_record


@router.get("/runs", response_model=List[RunSummaryResponse])
def list_runs(
    control_name: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List historical control runs with optional filtering.
    """
    query = db.query(ControlRunModel)
    if control_name:
        query = query.filter(ControlRunModel.control_name == control_name)
    if status_filter:
        query = query.filter(ControlRunModel.status == status_filter.upper())

    return query.order_by(ControlRunModel.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/runs/{run_id}", response_model=RunSummaryResponse)
def get_run_details(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve status and execution metrics for a specific run.
    """
    run_record = db.query(ControlRunModel).filter(ControlRunModel.run_id == run_id).first()
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found"
        )
    return run_record


@router.get("/runs/{run_id}/exceptions", response_model=PaginatedExceptionsResponse)
def get_run_exceptions(
    run_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated exception breaches for a specific control run.
    """
    run_record = db.query(ControlRunModel).filter(ControlRunModel.run_id == run_id).first()
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found"
        )

    exceptions_query = db.query(ControlExceptionModel).filter(
        ControlExceptionModel.run_id == run_id
    )
    total_breaches = exceptions_query.count()
    items = exceptions_query.offset(offset).limit(limit).all()

    return PaginatedExceptionsResponse(
        run_id=run_id,
        total_breaches=total_breaches,
        limit=limit,
        offset=offset,
        exceptions=[ExceptionItem.model_validate(item) for item in items]
    )
