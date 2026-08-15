class ControlRunner:
    def __init__(self, executor):
        self.executor = executor

    def run(self, component_name, data):
        if not component_name:
            raise ValueError("Control name cannot be empty")

        if data is None:
            raise ValueError("Control data cannot be None")

        if not isinstance(data, dict):
            raise ValueError("Control data must be a dictionary")

        return self.executor.run(component_name, data)