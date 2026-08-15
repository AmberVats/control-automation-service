import pytest

from src.components.registry import ComponentRegistry
from src.components.base import ControlComponent
from src.components.reconciliation import (
    two_way_match,
    TwoWayMatchControl,
)
from src.components.tolerance import check_tolerance, ToleranceControl


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


def test_registry_registers_component_using_metadata():
    registry = ComponentRegistry()

    component = ControlComponent(
        name="test.component",
        version="1.0"
    )

    registry.register(component)

    assert registry.get("test.component") is component

def test_registry_executes_registered_component():
    registry = ComponentRegistry()

    component = ToleranceControl()

    registry.register(component)

    result = registry.execute(
        "tolerance.threshold_check",
        {
            "expected": 100,
            "actual": 105,
            "tolerance": 10,
        },
    )

    assert result["status"] == "PASS"

def test_registry_execute_raises_error_for_unknown_component():
    registry = ComponentRegistry()

    with pytest.raises(KeyError):
        registry.execute(
            "unknown.component",
            {}
        )

def test_registry_executes_two_way_match_component():
    registry = ComponentRegistry()

    component = TwoWayMatchControl()

    registry.register(component)

    result = registry.execute(
        "reconciliation.two_way_match",
        {
            "source": [
                {
                    "as_of_date": "2026-08-09",
                    "instrument_id": "AAPL",
                    "book": "EQUITY_BOOK",
                    "quantity": 100,
                    "market_value": 20000,
                }
            ],
            "target": [
                {
                    "as_of_date": "2026-08-09",
                    "instrument_id": "AAPL",
                    "book": "EQUITY_BOOK",
                    "quantity": 100,
                    "market_value": 20000,
                }
            ],
            "keys": [
                "as_of_date",
                "instrument_id",
                "book",
            ],
            "compare": [
                "quantity",
                "market_value",
            ],
            "tolerance": {
                "quantity": {"absolute": 0},
                "market_value": {
                    "absolute": 50,
                    "relative": 0.0001,
                },
            },
        },
    )

    assert result["status"] == "PASS"
    assert result["breach_count"] == 0