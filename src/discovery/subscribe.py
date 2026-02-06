"""Subscribe state machine for NAN service discovery."""

import random
from enum import Enum
from typing import List, Optional


class SubscribeMode(Enum):
    """Subscribe modes."""
    ACTIVE = "active"      # Send SDF frames
    PASSIVE = "passive"    # Only listen


class SubscribedService:
    """Subscribed service instance."""

    def __init__(self, subscribe_id: int, service_name: str,
                 match_filter: Optional[bytes] = None, mode: SubscribeMode = SubscribeMode.ACTIVE):
        """Initialize subscribed service.

        Args:
            subscribe_id: Unique subscription identifier
            service_name: Name of service to subscribe to
            match_filter: Optional match filter
            mode: Active or passive mode
        """
        self.subscribe_id = subscribe_id
        self.service_name = service_name
        self.match_filter = match_filter
        self.mode = mode
        self.subscribe_count = 0

    def is_active(self) -> bool:
        """Check if subscription is active.

        Returns:
            True if subscription is active
        """
        return True  # Simplified - always active once created


class SubscribeStateMachine:
    """Subscribe state machine per NAN specification."""

    def __init__(self, env, node, config):
        """Initialize subscribe state machine.

        Args:
            env: SimPy environment
            node: NANNode instance
            config: Configuration dictionary
        """
        self.env = env
        self.node = node
        self.config = config

        self.subscribed_services: List[SubscribedService] = []
        self.subscribe_rate = config.get('traffic.subscribe_rate', 0.05)  # services/s
        self.service_pool = self._generate_service_pool()
        self.discovered_services = {}  # Track discovered services

    def _generate_service_pool(self) -> List[str]:
        """Generate pool of available service names.

        Returns:
            List of service names
        """
        service_count = self.config.get('traffic.service_count', 10)
        return [f"service_{i}" for i in range(service_count)]

    def run(self):
        """Main subscribe state machine loop."""
        while True:
            # Decide to subscribe to services
            if random.random() < self.subscribe_rate:
                self._subscribe_random_service()

            # Update subscribe counts
            self._update_subscribe_counts()

            # Wait for next cycle
            yield self.env.timeout(1000)  # Check every second

    def _subscribe_random_service(self) -> None:
        """Subscribe to a random service from the pool."""
        if not self.service_pool:
            return

        # Select random service
        service_name = random.choice(self.service_pool)
        subscribe_id = hash(f"{self.node.node_id}_{service_name}") % (2**32)

        # Create match filter (optional)
        match_filter = None
        if random.random() < 0.5:  # 50% chance of having match filter
            match_filter = bytes([random.randint(0, 255) for _ in range(8)])

        # Select mode
        mode = SubscribeMode.ACTIVE if random.random() < 0.7 else SubscribeMode.PASSIVE

        # Check if already subscribed
        existing = self.get_subscription_by_name(service_name)
        if existing is None:
            subscription = SubscribedService(
                subscribe_id=subscribe_id,
                service_name=service_name,
                match_filter=match_filter,
                mode=mode
            )
            self.subscribed_services.append(subscription)

            # Publish event
            self.node.event_bus.publish(
                'service_subscribed',
                node_id=self.node.node_id,
                subscribe_id=subscribe_id,
                service_name=service_name,
                mode=mode.value,
                timestamp=self.env.now
            )

    def unsubscribe(self, service_name: str) -> None:
        """Unsubscribe from a service.

        Args:
            service_name: Name of service to unsubscribe from
        """
        subscription = self.get_subscription_by_name(service_name)
        if subscription:
            self.subscribed_services.remove(subscription)

            self.node.event_bus.publish(
                'service_unsubscribed',
                node_id=self.node.node_id,
                subscribe_id=subscription.subscribe_id,
                service_name=service_name,
                timestamp=self.env.now
            )

    def _update_subscribe_counts(self) -> None:
        """Update subscribe count for all active subscriptions."""
        for subscription in self.subscribed_services:
            if subscription.is_active():
                subscription.subscribe_count += 1

    def process_discovery(self, publisher_id: int, service_name: str,
                         service_info: bytes, timestamp: float) -> None:
        """Process a service discovery event.

        Args:
            publisher_id: ID of publishing node
            service_name: Name of discovered service
            service_info: Service information bytes
            timestamp: Discovery timestamp
        """
        # Check if we're subscribed to this service
        subscription = self.get_subscription_by_name(service_name)

        if subscription:
            # Record discovery
            discovery_key = (publisher_id, service_name)

            if discovery_key not in self.discovered_services:
                self.discovered_services[discovery_key] = {
                    'publisher_id': publisher_id,
                    'service_name': service_name,
                    'service_info': service_info,
                    'discover_time': timestamp
                }

                # Publish discovery event
                self.node.event_bus.publish(
                    'service_discovered',
                    subscriber_id=self.node.node_id,
                    publisher_id=publisher_id,
                    service_name=service_name,
                    latency=timestamp,  # Time of discovery
                    timestamp=timestamp
                )

    def get_subscription_by_name(self, service_name: str) -> Optional[SubscribedService]:
        """Get subscription by service name.

        Args:
            service_name: Service name to search for

        Returns:
            SubscribedService if found, None otherwise
        """
        for subscription in self.subscribed_services:
            if subscription.service_name == service_name:
                return subscription
        return None

    def get_active_subscriptions(self) -> List[SubscribedService]:
        """Get all active subscriptions.

        Returns:
            List of active SubscribedService objects
        """
        return [s for s in self.subscribed_services if s.is_active()]

    def get_discovered_services(self) -> List[dict]:
        """Get all discovered services.

        Returns:
            List of discovery dictionaries
        """
        return list(self.discovered_services.values())
