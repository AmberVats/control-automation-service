import os
from pathlib import Path
from typing import List, Union
import yaml
from pydantic import ValidationError

from src.engine.schemas import ControlDefinitionSchema


def load_control_from_yaml_str(yaml_str: str) -> ControlDefinitionSchema:
    """Parse and validate a control definition from a YAML string."""
    try:
        data = yaml.safe_load(yaml_str)
    except Exception as e:
        raise ValueError(f"Invalid YAML syntax: {str(e)}")

    if not isinstance(data, dict):
        raise ValueError("YAML content must define a mapping/dictionary object")

    try:
        return ControlDefinitionSchema.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Control validation failed: {str(e)}")


def load_control_from_file(file_path: Union[str, Path]) -> ControlDefinitionSchema:
    """Load and validate a control definition from a YAML file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Control file not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    return load_control_from_yaml_str(content)


def load_controls_from_dir(dir_path: Union[str, Path]) -> List[ControlDefinitionSchema]:
    """Scan a directory for .yaml and .yml files and load all control definitions."""
    path = Path(dir_path)
    if not path.exists() or not path.is_dir():
        return []

    controls = []
    for file in sorted(path.glob("*")):
        if file.suffix.lower() in [".yaml", ".yml"]:
            try:
                control = load_control_from_file(file)
                controls.append(control)
            except Exception as e:
                # Log or re-raise
                print(f"Warning: Failed to load control from {file}: {e}")

    return controls
