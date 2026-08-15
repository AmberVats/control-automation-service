import pytest

from src.components.base import ControlComponent
from src.components.registry import ComponentRegistry


def test_control_component_requires_execute():
    component = ControlComponent(
        name="test.component",
        version="1.0"
    )

    with pytest.raises(NotImplementedError):
        component.execute({})


def test_control_component_has_name_and_version():
    component = ControlComponent(
        name="test.component",
        version="1.0"
    )

    assert component.name == "test.component"
    assert component.version == "1.0"


def test_control_component_rejects_empty_metadata():
    with pytest.raises(ValueError):
        ControlComponent(
            name="",
            version="1.0"
        )

    with pytest.raises(ValueError):
        ControlComponent(
            name="test.component",
            version=""
        )


def test_registry_rejects_component_without_required_metadata():
    registry = ComponentRegistry()

    with pytest.raises(ValueError):
        registry.register(object())