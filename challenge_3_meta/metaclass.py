class_registry = {}


class APIContractMeta(type):
    required_methods = []
    required_attributes = []

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        if name == 'BaseAPI':
            return cls

        for method in mcs.required_methods:
            if not callable(getattr(cls, method, None)):
                raise TypeError(f"Class '{name}' must implement method '{method}'")

        for attr in mcs.required_attributes:
            if not hasattr(cls, attr):
                raise AttributeError(f"Class '{name}' must define attribute '{attr}'")

        class_registry[name] = cls

        return cls


class BaseAPI(metaclass=APIContractMeta):
    pass