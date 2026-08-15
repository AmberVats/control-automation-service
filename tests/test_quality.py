import pytest
from datetime import date, datetime
from src.components.quality import (
    check_completeness,
    check_referential_integrity,
    check_staleness,
    CompletenessControl,
    ReferentialIntegrityControl,
    StalenessControl,
)


def test_completeness_pass():
    data = [
        {"id": 1, "ticker": "AAPL", "price": 150.0},
        {"id": 2, "ticker": "MSFT", "price": 310.0},
    ]
    result = check_completeness(data, required_fields=["id", "ticker", "price"])
    assert result["status"] == "PASS"
    assert result["breach_count"] == 0
    assert len(result["breaches"]) == 0


def test_completeness_missing_and_null():
    data = [
        {"id": 1, "ticker": "AAPL", "price": None},
        {"id": 2, "price": 310.0},
        {"id": 3, "ticker": "  ", "price": 200.0},
    ]
    result = check_completeness(data, required_fields=["id", "ticker", "price"])
    assert result["status"] == "BREACH"
    assert result["breach_count"] == 3

    types = [b["type"] for b in result["breaches"]]
    assert "NULL_VALUE" in types
    assert "MISSING_FIELD" in types
    assert "EMPTY_STRING" in types


def test_completeness_allow_empty_string():
    data = [{"id": 1, "comment": ""}]
    result = check_completeness(data, required_fields=["comment"], allow_empty_string=True)
    assert result["status"] == "PASS"


def test_referential_integrity_pass():
    source = [
        {"trade_id": "T1", "instrument_id": "INST_A"},
        {"trade_id": "T2", "instrument_id": "INST_B"},
    ]
    lookup = [
        {"instrument_id": "INST_A", "name": "Apple"},
        {"instrument_id": "INST_B", "name": "Microsoft"},
        {"instrument_id": "INST_C", "name": "Google"},
    ]
    result = check_referential_integrity(source, lookup, foreign_key="instrument_id")
    assert result["status"] == "PASS"
    assert result["breach_count"] == 0


def test_referential_integrity_breach():
    source = [
        {"trade_id": "T1", "instrument_id": "INST_A"},
        {"trade_id": "T2", "instrument_id": "INST_UNKNOWN"},
    ]
    lookup = [
        {"instrument_id": "INST_A"},
    ]
    result = check_referential_integrity(source, lookup, foreign_key="instrument_id")
    assert result["status"] == "BREACH"
    assert result["breach_count"] == 1
    assert result["breaches"][0]["foreign_key_value"] == "INST_UNKNOWN"


def test_referential_integrity_composite_key():
    source = [
        {"book": "LON_EQ", "ccy": "GBP"},
        {"book": "NY_EQ", "ccy": "EUR"},
    ]
    lookup = [
        {"book": "LON_EQ", "ccy": "GBP"},
        {"book": "NY_EQ", "ccy": "USD"},
    ]
    result = check_referential_integrity(
        source, lookup,
        foreign_key=["book", "ccy"],
        primary_key=["book", "ccy"]
    )
    assert result["status"] == "BREACH"
    assert result["breach_count"] == 1
    assert result["breaches"][0]["foreign_key_value"] == ("NY_EQ", "EUR")


def test_staleness_pass():
    data = [
        {"ticker": "AAPL", "price_date": "2026-08-15"},
        {"ticker": "MSFT", "price_date": "2026-08-14"},
    ]
    result = check_staleness(data, timestamp_field="price_date", as_of_date="2026-08-15", max_age_days=1)
    assert result["status"] == "PASS"
    assert result["breach_count"] == 0


def test_staleness_breach():
    data = [
        {"ticker": "AAPL", "price_date": "2026-08-15"},
        {"ticker": "STALE_STOCK", "price_date": "2026-08-10"},
    ]
    result = check_staleness(data, timestamp_field="price_date", as_of_date="2026-08-15", max_age_days=1)
    assert result["status"] == "BREACH"
    assert result["breach_count"] == 1
    assert result["breaches"][0]["type"] == "STALE_DATA"
    assert result["breaches"][0]["age_days"] == 5.0


def test_quality_control_classes():
    comp = CompletenessControl()
    assert comp.name == "quality.completeness"
    res_comp = comp.execute({"data": [{"x": 1}], "required_fields": ["x"]})
    assert res_comp["status"] == "PASS"

    ref = ReferentialIntegrityControl()
    assert ref.name == "quality.referential_integrity"
    res_ref = ref.execute({
        "source": [{"k": "A"}],
        "lookup": [{"k": "A"}],
        "foreign_key": "k"
    })
    assert res_ref["status"] == "PASS"

    stale = StalenessControl()
    assert stale.name == "quality.staleness"
    res_stale = stale.execute({
        "data": [{"dt": "2026-08-15"}],
        "timestamp_field": "dt",
        "as_of_date": "2026-08-15"
    })
    assert res_stale["status"] == "PASS"
