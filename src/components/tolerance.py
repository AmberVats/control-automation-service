from src.components.base import ControlComponent

def check_tolerance(expected, actual, tolerance):
    """
    Compare expected and actual values against an allowed tolerance.

    Returns:
        PASS if the absolute difference is within tolerance.
        FAIL if the difference exceeds tolerance.
    """

    difference = abs(actual - expected)

    if difference <= tolerance:
        status = "PASS"
    else:
        status = "FAIL"

    return {
        "status": status,
        "difference": difference
    }

class ToleranceControl(ControlComponent):
    def __init__(self, version="1.0"):
        super().__init__(
            name="tolerance.threshold_check",
            version=version,
        )

    def execute(self, data):
        return check_tolerance(**data)