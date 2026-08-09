import pytest

from src.components.registry import ComponentRegistry


def test_registry_registers_and_retrieves_component():
    registry = ComponentRegistry()
    component = object()

    registry.register("test.component", component)

    assert registry.get("test.component") is component


def test_registry_rejects_duplicate_component():
    registry = ComponentRegistry()

    registry.register("test.component", object())

    with pytest.raises(ValueError):
        registry.register("test.component", object())

def test_registry_raises_error_for_unknown_component():
    registry = ComponentRegistry()

    with pytest.raises(KeyError):
        registry.get("unknown.component")