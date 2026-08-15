import pytest

from src.components.registry import ComponentRegistry
from src.components.tolerance import ToleranceControl
from src.components.executor import ControlExecutor
from src.components.runner import ControlRunner


def test_control_runner_runs_control():
    registry = ComponentRegistry()
    registry.register(ToleranceControl())

    executor = ControlExecutor(registry)
    runner = ControlRunner(executor)

    result = runner.run(
        "tolerance.threshold_check",
        {
            "expected": 100,
            "actual": 105,
            "tolerance": 10,
        },
    )

    assert result["status"] == "PASS"
    assert result["difference"] == 5

def test_control_runner_propagates_unknown_control_error():
    registry = ComponentRegistry()

    executor = ControlExecutor(registry)
    runner = ControlRunner(executor)

    with pytest.raises(KeyError):
        runner.run(
            "unknown.control",
            {},
        )

def test_control_runner_rejects_empty_control_name():
    registry = ComponentRegistry()
    registry.register(ToleranceControl())

    executor = ControlExecutor(registry)
    runner = ControlRunner(executor)

    with pytest.raises(ValueError):
        runner.run(
            "",
            {
                "expected": 100,
                "actual": 105,
                "tolerance": 10,
            },
        )

def test_control_runner_rejects_missing_data():
    registry = ComponentRegistry()
    registry.register(ToleranceControl())

    executor = ControlExecutor(registry)
    runner = ControlRunner(executor)

    with pytest.raises(ValueError):
        runner.run(
            "tolerance.threshold_check",
            None,
        )

def test_control_runner_rejects_invalid_data_type():
    registry = ComponentRegistry()
    registry.register(ToleranceControl())

    executor = ControlExecutor(registry)
    runner = ControlRunner(executor)

    with pytest.raises(ValueError):
        runner.run(
            "tolerance.threshold_check",
            "invalid-data",
        )