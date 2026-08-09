class ControlComponent:
    def __init__(self, name, version):
        if not name:
            raise ValueError("Component name cannot be empty")

        if not version:
            raise ValueError("Component version cannot be empty")

        self.name = name
        self.version = version

    def execute(self, data):
        raise NotImplementedError