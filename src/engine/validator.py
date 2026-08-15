from typing import List, Tuple
from src.engine.schemas import ControlDefinitionSchema
from src.components.registry import ComponentRegistry


class ControlValidationError(ValueError):
    """Exception raised when control specification fails validation rules."""
    pass


def validate_control_against_registry(
    control: ControlDefinitionSchema,
    registry: ComponentRegistry
) -> Tuple[bool, List[str]]:
    """
    Validate a control definition against registered components and expected parameters.

    Returns:
        (is_valid: bool, error_messages: List[str])
    """
    errors = []

    # Check component registration
    if control.component not in registry.list_components():
        errors.append(
            f"Component '{control.component}' is not registered in the system. "
            f"Available components: {', '.join(registry.list_components())}"
        )
        return False, errors

    # Check specific component requirements
    if control.component == "reconciliation.two_way_match":
        if not control.keys:
            errors.append("Component 'reconciliation.two_way_match' requires 'keys' field")
        if not control.compare:
            errors.append("Component 'reconciliation.two_way_match' requires 'compare' field")

    elif control.component == "quality.completeness":
        if not control.parameters or "required_fields" not in control.parameters:
            if not control.compare and not control.keys:
                errors.append("Component 'quality.completeness' requires 'required_fields' in parameters")

    elif control.component == "quality.referential_integrity":
        if not control.parameters or "foreign_key" not in control.parameters:
            if not control.keys:
                errors.append("Component 'quality.referential_integrity' requires 'foreign_key' configuration")

    elif control.component == "quality.staleness":
        if not control.parameters or "timestamp_field" not in control.parameters:
            errors.append("Component 'quality.staleness' requires 'timestamp_field' in parameters")

    return len(errors) == 0, errors
