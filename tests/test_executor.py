from src.components.registry import ComponentRegistry
from src.components.tolerance import ToleranceControl
from src.components.executor import ControlExecutor


def test_executor_runs_registered_control():
    registry = ComponentRegistry()

    registry.register(ToleranceControl())

    executor = ControlExecutor(registry)

    result = executor.run(
        "tolerance.threshold_check",
        {
            "expected": 100,
            "actual": 105,
            "tolerance": 10,
        },
    )

    assert result["status"] == "PASS"
    assert result["difference"] == 5