import pytest
import os
from src.engine.schemas import ControlDefinitionSchema
from src.engine.loader import load_control_from_yaml_str, load_control_from_file, load_controls_from_dir
from src.engine.validator import validate_control_against_registry
from src.components.registry import ComponentRegistry


def test_schema_hashing_consistency():
    yaml_sample_1 = """
    name: eod_position_break
    version: 1
    component: reconciliation.two_way_match
    owner: pc_analytics
    """
    control1 = load_control_from_yaml_str(yaml_sample_1)
    control2 = load_control_from_yaml_str(yaml_sample_1)

    hash1 = control1.compute_hash()
    hash2 = control2.compute_hash()

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256


def test_schema_hashing_detects_changes():
    yaml_1 = """
    name: eod_position_break
    version: 1
    component: reconciliation.two_way_match
    """
    yaml_2 = """
    name: eod_position_break
    version: 2
    component: reconciliation.two_way_match
    """
    c1 = load_control_from_yaml_str(yaml_1)
    c2 = load_control_from_yaml_str(yaml_2)

    assert c1.compute_hash() != c2.compute_hash()


def test_load_control_from_yaml_str_valid():
    yaml_str = """
    name: eod_position_break
    version: 2
    component: reconciliation.two_way_match
    description: EOD positions check
    keys:
      - as_of_date
      - instrument_id
      - book
    compare:
      - quantity
      - market_value
    tolerance:
      quantity:
        absolute: 0
      market_value:
        absolute: 50
        relative: 0.0001
    """
    ctrl = load_control_from_yaml_str(yaml_str)
    assert ctrl.name == "eod_position_break"
    assert ctrl.version == 2
    assert ctrl.component == "reconciliation.two_way_match"
    assert ctrl.keys == ["as_of_date", "instrument_id", "book"]
    assert ctrl.compare == ["quantity", "market_value"]


def test_load_control_invalid_yaml():
    with pytest.raises(ValueError):
        load_control_from_yaml_str("name: [unclosed list")


def test_validate_control_against_registry():
    registry = ComponentRegistry.default()

    valid_ctrl = load_control_from_yaml_str("""
    name: test_ctrl
    component: reconciliation.two_way_match
    keys: [id]
    compare: [amount]
    """)
    is_valid, errors = validate_control_against_registry(valid_ctrl, registry)
    assert is_valid is True
    assert len(errors) == 0

    invalid_comp = load_control_from_yaml_str("""
    name: test_ctrl
    component: non_existent_comp
    """)
    is_valid, errors = validate_control_against_registry(invalid_comp, registry)
    assert is_valid is False
    assert any("not registered" in err for err in errors)
