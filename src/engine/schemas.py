import hashlib
import json
import yaml
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class DataSourceConfig(BaseModel):
    type: str = "inline"  # inline, sql, file, query_file
    connection: Optional[str] = None
    query: Optional[str] = None
    query_file: Optional[str] = None
    file_path: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None


class ToleranceConfig(BaseModel):
    absolute: Optional[float] = 0.0
    relative: Optional[float] = 0.0
    max_days: Optional[float] = None
    description: Optional[str] = None


class ControlDefinitionSchema(BaseModel):
    name: str = Field(..., min_length=1, description="Unique identifier for the control")
    version: Union[int, str] = Field(default=1, description="Version of the control definition")
    component: str = Field(..., min_length=1, description="Registered component name to execute")
    description: Optional[str] = None
    owner: Optional[str] = "product_control_analytics"
    schedule: Optional[str] = None
    enabled: bool = True
    source: Optional[Union[DataSourceConfig, Dict[str, Any]]] = None
    target: Optional[Union[DataSourceConfig, Dict[str, Any]]] = None
    lookup: Optional[Union[DataSourceConfig, Dict[str, Any]]] = None
    keys: Optional[List[str]] = None
    compare: Optional[List[str]] = None
    tolerance: Optional[Dict[str, Union[ToleranceConfig, Dict[str, Any], float]]] = None
    parameters: Optional[Dict[str, Any]] = None
    notify: Optional[Dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Control name cannot be blank")
        return v.strip()

    @field_validator("component")
    @classmethod
    def validate_component(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Component cannot be blank")
        return v.strip()

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 hash of configuration."""
        raw_dict = self.model_dump(mode="json", exclude_none=True)
        canonical_str = json.dumps(raw_dict, sort_keys=True)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def to_yaml(self) -> str:
        """Dump model to YAML string."""
        return yaml.dump(self.model_dump(mode="json", exclude_none=True), sort_keys=False)
