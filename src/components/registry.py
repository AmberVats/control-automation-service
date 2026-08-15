class ComponentRegistry:
    def __init__(self):
        self._components = {}

    def register(self, name_or_component, component=None):
        if component is None:
            component = name_or_component
            name = component.name
        else:
            name = name_or_component

        if name in self._components:
            raise ValueError(f"Component already registered: {name}")

        self._components[name] = component

    def get(self, name):
        return self._components[name]

    def list_components(self):
        return list(self._components.keys())