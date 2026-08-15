from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class ControlRegisterRequest(BaseModel):
    yaml_content: Optional[str] = Field(None, description="Raw YAML string defining the control")
    definition: Optional[Dict[str, Any]] = Field(None, description="Direct JSON representation of the control")


class ControlResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    version: str
    component: str
    description: Optional[str] = None
    owner: Optional[str] = None
    schedule: Optional[str] = None
    config_hash: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ControlDetailResponse(ControlResponse):
    config_yaml: str


class ControlRunRequest(BaseModel):
    as_of_date: Optional[str] = Field(None, description="As-of date in YYYY-MM-DD format")
    triggered_by: Optional[str] = Field("api", description="Source or user triggering execution")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional override payload for in-flight validation")


class ExceptionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    run_id: str
    exception_type: str
    key_data: Optional[str] = None
    field: Optional[str] = None
    source_val: Optional[str] = None
    target_val: Optional[str] = None
    difference: Optional[float] = None
    message: Optional[str] = None
    created_at: datetime


class RunSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    control_name: str
    version: str
    config_hash: str
    status: str
    triggered_by: str
    as_of_date: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    row_count_in: int
    row_count_out: int
    breach_count: int
    error_message: Optional[str] = None
    created_at: datetime


class PaginatedExceptionsResponse(BaseModel):
    run_id: str
    total_breaches: int
    limit: int
    offset: int
    exceptions: List[ExceptionItem]


class ComponentCatalogueItem(BaseModel):
    name: str
    version: str
    category: str
    description: str
    required_parameters: List[str]
    optional_parameters: List[str]


class ServiceMetricsResponse(BaseModel):
    status: str
    total_registered_controls: int
    total_runs_executed: int
    pass_rate_percentage: float
    total_breaches_detected: int
    average_duration_ms: float
