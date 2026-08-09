from src.components.tolerance import check_tolerance


def test_tolerance_passes_when_difference_is_within_limit():
    result = check_tolerance(
        expected=1000.00,
        actual=1000.50,
        tolerance=1.00
    )

    assert result["status"] == "PASS"
    assert result["difference"] == 0.50


def test_tolerance_fails_when_difference_exceeds_limit():
    result = check_tolerance(
        expected=1000.00,
        actual=1002.00,
        tolerance=1.00
    )

    assert result["status"] == "FAIL"
    assert result["difference"] == 2.00