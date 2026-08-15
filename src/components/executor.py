class ControlExecutor:
    def __init__(self, registry):
        self.registry = registry

    def run(self, component_name, data):
        return self.registry.execute(component_name, data)