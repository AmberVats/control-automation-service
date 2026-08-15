from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.models import ControlModel
from src.engine.schemas import ControlDefinitionSchema
from src.engine.loader import load_control_from_yaml_str
from src.engine.validator import validate_control_against_registry
from src.components.registry import ComponentRegistry
from src.api.schemas import (
    ControlRegisterRequest,
    ControlResponse,
    ControlDetailResponse,
)

router = APIRouter(prefix="/controls", tags=["Controls"])


@router.post("", response_model=ControlResponse, status_code=status.HTTP_201_CREATED)
def register_control(
    request: ControlRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register or update a financial control from YAML specification or JSON.
    """
    try:
        if request.yaml_content:
            control_def = load_control_from_yaml_str(request.yaml_content)
            yaml_raw = request.yaml_content
        elif request.definition:
            control_def = ControlDefinitionSchema.model_validate(request.definition)
            yaml_raw = control_def.to_yaml()
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either 'yaml_content' or 'definition' must be provided"
            )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    # Validate against component registry
    registry = ComponentRegistry.default()
    is_valid, errors = validate_control_against_registry(control_def, registry)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Control failed validation", "errors": errors}
        )

    config_hash = control_def.compute_hash()

    # Check if control exists
    existing = db.query(ControlModel).filter(ControlModel.name == control_def.name).first()
    if existing:
        existing.version = str(control_def.version)
        existing.component = control_def.component
        existing.description = control_def.description
        existing.owner = control_def.owner
        existing.schedule = control_def.schedule
        existing.config_yaml = yaml_raw
        existing.config_hash = config_hash
        existing.enabled = control_def.enabled
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_control = ControlModel(
            name=control_def.name,
            version=str(control_def.version),
            component=control_def.component,
            description=control_def.description,
            owner=control_def.owner,
            schedule=control_def.schedule,
            config_yaml=yaml_raw,
            config_hash=config_hash,
            enabled=control_def.enabled
        )
        db.add(new_control)
        db.commit()
        db.refresh(new_control)
        return new_control


@router.get("", response_model=List[ControlResponse])
def list_controls(
    owner: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List all registered controls in the Citizen Developer catalogue.
    """
    query = db.query(ControlModel)
    if owner:
        query = query.filter(ControlModel.owner == owner)
    if enabled is not None:
        query = query.filter(ControlModel.enabled == enabled)

    return query.order_by(ControlModel.name).all()


@router.get("/{name}", response_model=ControlDetailResponse)
def get_control_details(
    name: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve full metadata and YAML specification for a registered control.
    """
    control = db.query(ControlModel).filter(ControlModel.name == name).first()
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control '{name}' not found"
        )
    return control
