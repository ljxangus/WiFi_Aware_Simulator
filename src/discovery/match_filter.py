"""Service matching logic for NAN discovery."""

from typing import List, Optional, Any
from dataclasses import dataclass


@dataclass
class Service:
    """NAN Service definition."""
    service_id: int
    service_name: str
    service_info: bytes
    match_filter: Optional[bytes] = None
    publish_count: int = 0

    def matches(self, filter_pattern: bytes) -> bool:
        """Check if service matches filter pattern.

        Args:
            filter_pattern: Match filter to compare against

        Returns:
            True if service matches filter
        """
        if self.match_filter is None:
            return True  # No filter means match all

        return self.match_filter == filter_pattern


@dataclass
class ServiceSubscription:
    """Service subscription (Subscribe side)."""
    subscribe_id: int
    service_name: str
    match_filter: Optional[bytes] = None
    subscribe_count: int = 0


class MatchFilter:
    """Service matching engine."""

    def __init__(self):
        """Initialize match filter."""
        self.matches = []  # List of discovered matches

    def find_matches(self, published_services: List[Service],
                    subscribed_services: List[ServiceSubscription]) -> List[dict]:
        """Find matching services between published and subscribed.

        Args:
            published_services: List of published services
            subscribed_services: List of subscribed services

        Returns:
            List of match dictionaries
        """
        matches = []

        for pub in published_services:
            for sub in subscribed_services:
                if self._service_match(pub, sub):
                    matches.append({
                        'publisher_id': pub.service_id,
                        'subscriber_id': sub.subscribe_id,
                        'service_name': pub.service_name,
                        'match_filter': pub.match_filter,
                        'service_info': pub.service_info
                    })

        return matches

    def _service_match(self, published: Service, subscribed: ServiceSubscription) -> bool:
        """Check if published service matches subscription.

        Args:
            published: Published service
            subscribed: Service subscription

        Returns:
            True if service matches subscription
        """
        # Service name must match
        if published.service_name != subscribed.service_name:
            return False

        # Match filter must match (if specified)
        if subscribed.match_filter is not None:
            if not published.matches(subscribed.match_filter):
                return False

        return True

    def add_match(self, publisher_id: int, subscriber_id: int,
                  service_name: str, timestamp: float) -> None:
        """Record a service match.

        Args:
            publisher_id: Publisher node ID
            subscriber_id: Subscriber node ID
            service_name: Name of matched service
            timestamp: Match timestamp (ms)
        """
        self.matches.append({
            'publisher_id': publisher_id,
            'subscriber_id': subscriber_id,
            'service_name': service_name,
            'timestamp': timestamp
        })

    def get_matches_for_service(self, service_name: str) -> List[dict]:
        """Get all matches for a specific service.

        Args:
            service_name: Service name to filter by

        Returns:
            List of matches for the service
        """
        return [m for m in self.matches if m['service_name'] == service_name]

    def clear(self) -> None:
        """Clear all matches."""
        self.matches.clear()
