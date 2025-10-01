import pytest
from metaclass import (
    APIContractMeta,
    ServiceMeta,
    ProcessorMeta,
    HandlerMeta,
    class_registry
)


class TestValidClassCreation:
    def test_valid_service_class(self):
        """Bird can start and stop, has a name"""
        class Bird(metaclass=ServiceMeta):
            name = "tweety"

            def start(self):
                return "flying"

            def stop(self):
                return "landing"

        assert "Bird" in class_registry
        assert class_registry["Bird"] is Bird

    def test_valid_processor_class(self):
        """Vacuum processes and validates, has version"""
        class Vacuum(metaclass=ProcessorMeta):
            version = "2.0"

            def process(self, dirt):
                return f"cleaning {dirt}"

            def validate(self):
                return True

        assert "Vacuum" in class_registry

    def test_valid_handler_class(self):
        """Doorbell handles and cleans up"""
        class Doorbell(metaclass=HandlerMeta):
            def handle(self, ring):
                return "ding dong"

            def cleanup(self):
                pass

        assert "Doorbell" in class_registry


class TestMissingMethodValidation:
    def test_missing_method_raises_error(self):
        """BrokenBird missing stop method"""
        with pytest.raises(TypeError, match="must implement method 'stop'"):
            class BrokenBird(metaclass=ServiceMeta):
                name = "broken"

                def start(self):
                    pass

    def test_missing_multiple_methods(self):
        """LazyRobot missing all methods"""
        with pytest.raises(TypeError, match="must implement method"):
            class LazyRobot(metaclass=ProcessorMeta):
                version = "1.0"


class TestMissingAttributeValidation:
    def test_missing_attribute_raises_error(self):
        """AnonymousBird missing name attribute"""
        with pytest.raises(AttributeError, match="must define attribute 'name'"):
            class AnonymousBird(metaclass=ServiceMeta):
                def start(self):
                    pass

                def stop(self):
                    pass

    def test_missing_version_attribute(self):
        """OldProcessor missing version"""
        with pytest.raises(AttributeError, match="must define attribute 'version'"):
            class OldProcessor(metaclass=ProcessorMeta):
                def process(self, data):
                    pass

                def validate(self):
                    pass


class TestInheritance:
    def test_method_inheritance(self):
        """Penguin inherits flying abilities from Bird"""
        class Bird(metaclass=ServiceMeta):
            name = "generic bird"

            def start(self):
                return "flying"

            def stop(self):
                return "landing"

        class Penguin(Bird):
            name = "penguin"

        assert "Penguin" in class_registry
        penguin = Penguin()
        assert penguin.start() == "flying"

    def test_attribute_inheritance(self):
        """RobotV2 inherits version from RobotV1"""
        class RobotV1(metaclass=ProcessorMeta):
            version = "1.0"

            def process(self, data):
                return data

            def validate(self):
                return True

        class RobotV2(RobotV1):
            pass

        assert "RobotV2" in class_registry
        assert RobotV2.version == "1.0"

    def test_partial_inheritance(self):
        """Dog inherits and overrides from Animal"""
        class Animal(metaclass=ServiceMeta):
            name = "animal"

            def start(self):
                return "moving"

            def stop(self):
                return "stopping"

        class Dog(Animal):
            name = "dog"

            def stop(self):
                return "sitting"

        assert "Dog" in class_registry
        dog = Dog()
        assert dog.start() == "moving"
        assert dog.stop() == "sitting"


class TestRegistry:
    def test_multiple_metaclasses_registered(self):
        """Registry contains classes from different metaclasses"""
        initial_count = len(class_registry)

        class Sparrow(metaclass=ServiceMeta):
            name = "sparrow"

            def start(self):
                pass

            def stop(self):
                pass

        class Blender(metaclass=ProcessorMeta):
            version = "3.0"

            def process(self, food):
                pass

            def validate(self):
                pass

        class Microwave(metaclass=HandlerMeta):
            def handle(self, food):
                pass

            def cleanup(self):
                pass

        assert len(class_registry) == initial_count + 3
        assert "Sparrow" in class_registry
        assert "Blender" in class_registry
        assert "Microwave" in class_registry

    def test_registry_contains_correct_references(self):
        """Registry stores actual class references"""
        class Eagle(metaclass=ServiceMeta):
            name = "eagle"

            def start(self):
                pass

            def stop(self):
                pass

        assert class_registry["Eagle"] is Eagle


class TestEdgeCases:
    def test_empty_contract_metaclass(self):
        """No requirements should register without validation"""
        class EmptyMeta(APIContractMeta):
            pass

        class Whatever(metaclass=EmptyMeta):
            pass

        assert "Whatever" in class_registry

    def test_multiple_inheritance(self):
        """Class inheriting from multiple parents"""
        class Flyer:
            def start(self):
                return "taking off"

        class Swimmer:
            def stop(self):
                return "diving"

        class Duck(Flyer, Swimmer, metaclass=ServiceMeta):
            name = "duck"

        assert "Duck" in class_registry
        duck = Duck()
        assert duck.start() == "taking off"
        assert duck.stop() == "diving"
