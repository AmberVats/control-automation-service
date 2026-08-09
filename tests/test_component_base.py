import pytest

from src.components.base import ControlComponent


def test_control_component_requires_execute():
    component = ControlComponent()

    with pytest.raises(NotImplementedError):
        component.execute({})