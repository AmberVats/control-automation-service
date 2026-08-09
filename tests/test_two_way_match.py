from src.components.reconciliation import two_way_match


def test_two_way_match_passes_when_values_match():
    source = [
        {
            "as_of_date": "2026-08-09",
            "instrument_id": "AAPL",
            "book": "EQUITY_BOOK",
            "quantity": 100,
            "market_value": 20000,
        }
    ]

    target = [
        {
            "as_of_date": "2026-08-09",
            "instrument_id": "AAPL",
            "book": "EQUITY_BOOK",
            "quantity": 100,
            "market_value": 20000,
        }
    ]

    result = two_way_match(
        source=source,
        target=target,
        keys=["as_of_date", "instrument_id", "book"],
        compare=["quantity", "market_value"],
        tolerance={
            "quantity": {"absolute": 0},
            "market_value": {
                "absolute": 50,
                "relative": 0.0001,
            },
        },
    )

    assert result["status"] == "PASS"
    assert result["breach_count"] == 0


def test_two_way_match_detects_market_value_break():
    source = [
        {
            "as_of_date": "2026-08-09",
            "instrument_id": "AAPL",
            "book": "EQUITY_BOOK",
            "quantity": 100,
            "market_value": 20000,
        }
    ]

    target = [
        {
            "as_of_date": "2026-08-09",
            "instrument_id": "AAPL",
            "book": "EQUITY_BOOK",
            "quantity": 100,
            "market_value": 20200,
        }
    ]

    result = two_way_match(
        source=source,
        target=target,
        keys=["as_of_date", "instrument_id", "book"],
        compare=["quantity", "market_value"],
        tolerance={
            "quantity": {"absolute": 0},
            "market_value": {
                "absolute": 50,
                "relative": 0.0001,
            },
        },
    )

    assert result["status"] == "BREACH"
    assert result["breach_count"] == 1