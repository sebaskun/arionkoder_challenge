import logging
import time
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceManager:
    """Context manager for handling multiple external resources with cleanup and metrics."""

    def __init__(self, name: str):
        self.name = name
        self.resources: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def add_resource(self, resource_name: str, resource: Any) -> None:
        """Add a resource to be managed."""
        self.resources[resource_name] = resource
        logger.info(f"[{self.name}] Added resource: {resource_name}")

    def __enter__(self) -> "ResourceManager":
        """Enter the context - initialize resources and start timing."""
        self.start_time = time.time()
        logger.info(f"[{self.name}] Context entered")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the context - cleanup resources and log metrics."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        # Handle exceptions
        if exc_type is not None:
            logger.error(f"[{self.name}] Exception occurred: {exc_type.__name__}: {exc_val}")

        # Cleanup all resources
        for resource_name, resource in self.resources.items():
            try:
                if hasattr(resource, 'close'):
                    resource.close()
                    logger.info(f"[{self.name}] Closed resource: {resource_name}")
            except Exception as e:
                logger.error(f"[{self.name}] Error closing {resource_name}: {e}")

        # Log performance metrics
        logger.info(f"[{self.name}] Context exited - Duration: {duration:.4f}s")

        # Don't suppress exceptions
        return False