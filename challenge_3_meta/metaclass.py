class_registry = {}


class APIContractMeta(type):
    required_methods = []
    required_attributes = []

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        # Skip validation for base metaclass instances
        if not mcs.required_methods and not mcs.required_attributes:
            class_registry[name] = cls
            return cls

        # Validate required methods (check through MRO for inheritance)
        for method in mcs.required_methods:
            method_found = False
            for base in cls.__mro__:
                if method in base.__dict__ and callable(base.__dict__[method]):
                    method_found = True
                    break

            if not method_found:
                raise TypeError(
                    f"Class '{name}' must implement method '{method}'. "
                    f"Required by {mcs.__name__}."
                )

        # Validate required attributes (check through MRO for inheritance)
        for attr in mcs.required_attributes:
            if not any(attr in base.__dict__ for base in cls.__mro__):
                raise AttributeError(
                    f"Class '{name}' must define attribute '{attr}'. "
                    f"Required by {mcs.__name__}."
                )

        class_registry[name] = cls
        return cls


class ServiceMeta(APIContractMeta):
    required_methods = ['start', 'stop']
    required_attributes = ['name']


class ProcessorMeta(APIContractMeta):
    required_methods = ['process', 'validate']
    required_attributes = ['version']


class HandlerMeta(APIContractMeta):
    required_methods = ['handle', 'cleanup']