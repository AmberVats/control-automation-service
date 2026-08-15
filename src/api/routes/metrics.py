from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db.session import get_db
from src.db.models import ControlModel, ControlRunModel
from src.api.schemas import ServiceMetricsResponse

router = APIRouter(tags=["Health & Monitoring"])


@router.get("/health")
def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "control-automation-service",
        "version": "1.0.0"
    }


@router.get("/metrics", response_model=ServiceMetricsResponse)
def get_service_metrics(db: Session = Depends(get_db)):
    """
    Observability and aggregate control performance metrics.
    """
    total_controls = db.query(ControlModel).count()
    total_runs = db.query(ControlRunModel).count()
    pass_runs = db.query(ControlRunModel).filter(ControlRunModel.status == "PASS").count()
    total_breaches = db.query(func.sum(ControlRunModel.breach_count)).scalar() or 0
    avg_duration = db.query(func.avg(ControlRunModel.duration_ms)).scalar() or 0.0

    pass_rate = (pass_runs / total_runs * 100.0) if total_runs > 0 else 100.0

    return ServiceMetricsResponse(
        status="operational",
        total_registered_controls=total_controls,
        total_runs_executed=total_runs,
        pass_rate_percentage=round(pass_rate, 2),
        total_breaches_detected=int(total_breaches),
        average_duration_ms=round(float(avg_duration), 2)
    )
