class ControlConfig:
    def __init__(self, name, version, enabled):
        if not name:
            raise ValueError("Control name cannot be empty")

        if not version:
            raise ValueError("Control version cannot be empty")

        if not isinstance(enabled, bool):
            raise ValueError("Control enabled flag must be a boolean")

        self.name = name
        self.version = version
        self.enabled = enabled