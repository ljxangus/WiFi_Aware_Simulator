"""Publish state machine for NAN service discovery."""

import random
from enum import Enum
from typing import List, Optional


class PublishState(Enum):
    """Publish service states."""
    INACTIVE = "inactive"
    ACTIVE = "active"


class PublishedService:
    """Published service instance."""

    def __init__(self, service_id: int, service_name: str,
                 service_info: bytes, match_filter: Optional[bytes] = None):
        """Initialize published service.

        Args:
            service_id: Unique service identifier
            service_name: Name of the service
            service_info: Service information bytes
            match_filter: Optional match filter
        """
        self.service_id = service_id
        self.service_name = service_name
        self.service_info = service_info
        self.match_filter = match_filter
        self.publish_count = 0
        self.state = PublishState.INACTIVE

    def activate(self) -> None:
        """Activate service publishing."""
        self.state = PublishState.ACTIVE

    def deactivate(self) -> None:
        """Deactivate service publishing."""
        self.state = PublishState.INACTIVE

    def is_active(self) -> bool:
        """Check if service is active.

        Returns:
            True if service is active
        """
        return self.state == PublishState.ACTIVE


class PublishStateMachine:
    """Publish service state machine per NAN specification."""

    def __init__(self, env, node, config):
        """Initialize publish state machine.

        Args:
            env: SimPy environment
            node: NANNode instance
            config: Configuration dictionary
        """
        self.env = env
        self.node = node
        self.config = config

        self.published_services: List[PublishedService] = []
        self.publish_rate = config.get('traffic.publish_rate', 0.1)  # services/s
        self.service_pool = self._generate_service_pool()

    def _generate_service_pool(self) -> List[str]:
        """Generate pool of available service names.

        Returns:
            List of service names
        """
        service_count = self.config.get('traffic.service_count', 10)
        return [f"service_{i}" for i in range(service_count)]

    def run(self):
        """Main publish state machine loop."""
        while True:
            # Decide to publish/unpublish services
            if random.random() < self.publish_rate:
                self._publish_random_service()

            # Update publish counts
            self._update_publish_counts()

            # Wait for next cycle
            yield self.env.timeout(1000)  # Check every second

    def _publish_random_service(self) -> None:
        """Publish a random service from the pool."""
        if not self.service_pool:
            return

        # Select random service
        service_name = random.choice(self.service_pool)
        service_id = hash(service_name) % (2**32)

        # Create service info
        payload_size = self.config.get('traffic.payload_size', 256)
        service_info = bytes([random.randint(0, 255) for _ in range(payload_size)])

        # Create match filter (optional)
        match_filter = None
        if random.random() < 0.5:  # 50% chance of having match filter
            match_filter = bytes([random.randint(0, 255) for _ in range(8)])

        # Check if already publishing
        existing = self.get_service_by_name(service_name)
        if existing:
            existing.activate()
        else:
            service = PublishedService(
                service_id=service_id,
                service_name=service_name,
                service_info=service_info,
                match_filter=match_filter
            )
            service.activate()
            self.published_services.append(service)

            # Publish event
            self.node.event_bus.publish(
                'service_published',
                node_id=self.node.node_id,
                service_id=service_id,
                service_name=service_name,
                timestamp=self.env.now
            )

    def unpublish_service(self, service_name: str) -> None:
        """Stop publishing a service.

        Args:
            service_name: Name of service to unpublish
        """
        service = self.get_service_by_name(service_name)
        if service:
            service.deactivate()

            self.node.event_bus.publish(
                'service_unpublished',
                node_id=self.node.node_id,
                service_id=service.service_id,
                service_name=service_name,
                timestamp=self.env.now
            )

    def _update_publish_counts(self) -> None:
        """Update publish count for all active services."""
        for service in self.published_services:
            if service.is_active():
                service.publish_count += 1

    def get_service_by_name(self, service_name: str) -> Optional[PublishedService]:
        """Get published service by name.

        Args:
            service_name: Service name to search for

        Returns:
            PublishedService if found, None otherwise
        """
        for service in self.published_services:
            if service.service_name == service_name:
                return service
        return None

    def get_active_services(self) -> List[PublishedService]:
        """Get all active published services.

        Returns:
            List of active PublishedService objects
        """
        return [s for s in self.published_services if s.is_active()]

    def has_active_services(self) -> bool:
        """Check if any services are actively published.

        Returns:
            True if at least one service is active
        """
        return any(s.is_active() for s in self.published_services)
