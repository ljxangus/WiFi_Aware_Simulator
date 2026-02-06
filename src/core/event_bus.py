"""Event bus for collecting simulation statistics and events."""

from typing import Callable, Dict, List, Any
from collections import defaultdict


class EventBus:
    """Central event bus for simulation-wide event handling."""

    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_log: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Type of event (e.g., 'discovery', 'power_state_change')
            callback: Function to call when event occurs
        """
        self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, **kwargs) -> None:
        """Publish an event to all subscribers.

        Args:
            event_type: Type of event
            **kwargs: Event data
        """
        # Log event
        event = {'type': event_type, 'data': kwargs}
        self._event_log.append(event)

        # Notify subscribers
        for callback in self._subscribers[event_type]:
            callback(**kwargs)

    def get_events(self, event_type: str = None) -> List[Dict[str, Any]]:
        """Get logged events, optionally filtered by type.

        Args:
            event_type: Filter by event type. If None, return all events.

        Returns:
            List of events
        """
        if event_type is None:
            return self._event_log.copy()

        return [e for e in self._event_log if e['type'] == event_type]

    def clear(self) -> None:
        """Clear all logged events."""
        self._event_log.clear()
