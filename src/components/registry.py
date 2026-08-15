from src.components.reconciliation import TwoWayMatchControl
from src.components.tolerance import ToleranceControl
from src.components.quality import (
    CompletenessControl,
    ReferentialIntegrityControl,
    StalenessControl,
)


class ComponentRegistry:

    def __init__(self):
        self._components = {}

    def register(self, name_or_component, component=None):
        if component is None:
            component = name_or_component

            if not hasattr(component, "name"):
                raise ValueError("Component must have a name")

            if not hasattr(component, "version"):
                raise ValueError("Component must have a version")

            if not component.name:
                raise ValueError("Component name cannot be empty")

            if not component.version:
                raise ValueError("Component version cannot be empty")

            name = component.name

        else:
            name = name_or_component

        if name in self._components:
            raise ValueError(f"Component already registered: {name}")

        self._components[name] = component

    def get(self, name):
        return self._components[name]

    def list_components(self):
        return list(self._components.keys())

    def get_catalogue(self):
        """Return a structured metadata catalogue of registered components."""
        catalogue = []
        metadata_map = {
            "reconciliation.two_way_match": {
                "name": "reconciliation.two_way_match",
                "version": "1.0",
                "category": "reconciliation",
                "description": "Two-way matching between source and target datasets with composite keys and field tolerances.",
                "required_parameters": ["source", "target", "keys", "compare"],
                "optional_parameters": ["tolerance"]
            },
            "tolerance.threshold_check": {
                "name": "tolerance.threshold_check",
                "version": "1.0",
                "category": "tolerance",
                "description": "Threshold check comparing expected vs actual values within an absolute tolerance.",
                "required_parameters": ["expected", "actual", "tolerance"],
                "optional_parameters": []
            },
            "quality.completeness": {
                "name": "quality.completeness",
                "version": "1.0",
                "category": "quality",
                "description": "Check dataset for missing, null, or empty string values in required fields.",
                "required_parameters": ["data", "required_fields"],
                "optional_parameters": ["allow_empty_string"]
            },
            "quality.referential_integrity": {
                "name": "quality.referential_integrity",
                "version": "1.0",
                "category": "quality",
                "description": "Ensure foreign key relationships hold between source records and parent lookup tables.",
                "required_parameters": ["source", "lookup", "foreign_key"],
                "optional_parameters": ["primary_key"]
            },
            "quality.staleness": {
                "name": "quality.staleness",
                "version": "1.0",
                "category": "quality",
                "description": "Ensure timestamps or dates in data are within maximum allowed age relative to as_of_date.",
                "required_parameters": ["data", "timestamp_field", "as_of_date"],
                "optional_parameters": ["max_age_days", "date_format"]
            }
        }

        for name, comp in self._components.items():
            if name in metadata_map:
                catalogue.append(metadata_map[name])
            else:
                ver = getattr(comp, "version", "1.0")
                catalogue.append({
                    "name": name,
                    "version": ver,
                    "category": name.split(".")[0] if "." in name else "custom",
                    "description": getattr(comp, "__doc__", "") or f"Control component {name}",
                    "required_parameters": [],
                    "optional_parameters": []
                })
        return catalogue

    def execute(self, name, data):
        component = self.get(name)
        if hasattr(component, "execute"):
            return component.execute(data)
        elif callable(component):
            return component(**data)
        raise TypeError(f"Component '{name}' is not executable")

    @classmethod
    def default(cls):
        """Create a ComponentRegistry pre-populated with standard library components."""
        registry = cls()
        registry.register(TwoWayMatchControl())
        registry.register(ToleranceControl())
        registry.register(CompletenessControl())
        registry.register(ReferentialIntegrityControl())
        registry.register(StalenessControl())
        return registry