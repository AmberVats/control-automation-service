import pytest

from src.components.registry import ComponentRegistry
from src.components.reconciliation import two_way_match
from src.components.tolerance import check_tolerance


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

def test_registry_registers_two_way_match_component():
    registry = ComponentRegistry()

    registry.register(
        "reconciliation.two_way_match",
        two_way_match
    )

    assert registry.get("reconciliation.two_way_match") is two_way_match

def test_registry_registers_tolerance_component():
    registry = ComponentRegistry()

    registry.register(
        "tolerance.threshold_check",
        check_tolerance
    )

    assert registry.get("tolerance.threshold_check") is check_tolerance

def test_registry_lists_registered_components():
    registry = ComponentRegistry()

    registry.register("reconciliation.two_way_match", two_way_match)
    registry.register("tolerance.threshold_check", check_tolerance)

    assert registry.list_components() == [
        "reconciliation.two_way_match",
        "tolerance.threshold_check",
    ]