import pytest

from src.components.config import ControlConfig


def test_control_config_loads_control_definition():
    config = ControlConfig(
        name="tolerance.threshold_check",
        version="1.0",
        enabled=True,
    )

    assert config.name == "tolerance.threshold_check"
    assert config.version == "1.0"
    assert config.enabled is True


def test_control_config_rejects_empty_name():
    with pytest.raises(ValueError):
        ControlConfig(
            name="",
            version="1.0",
            enabled=True,
        )

def test_control_config_rejects_empty_version():
    with pytest.raises(ValueError):
        ControlConfig(
            name="tolerance.threshold_check",
            version="",
            enabled=True,
        )

def test_control_config_rejects_invalid_enabled_value():
    with pytest.raises(ValueError):
        ControlConfig(
            name="tolerance.threshold_check",
            version="1.0",
            enabled="yes",
        )