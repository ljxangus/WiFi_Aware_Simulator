"""NDP Schedule negotiation for NAN data path."""

from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class NDPSchedule:
    """NDP Schedule for Post-DW availability."""
    ndp_id: int
    channel: int
    start_time: int  # Relative to DW end (ms)
    duration: int    # Duration (ms)
    peer_id: int


class NDPScheduleNegotiator:
    """NDP Schedule negotiator per WFA NAN specification."""

    def __init__(self, env, node, config):
        """Initialize schedule negotiator.

        Args:
            env: SimPy environment
            node: NANNode instance
            config: Configuration dictionary
        """
        self.env = env
        self.node = node
        self.config = config

        self.outgoing_schedules: List[NDPSchedule] = []
        self.incoming_schedules: List[NDPSchedule] = []
        self.schedule_id_counter = 0

    def create_schedule(self, ndp_id: int, channel: int,
                       start_time: int, duration: int, peer_id: int) -> NDPSchedule:
        """Create a new NDP schedule.

        Args:
            ndp_id: NDP instance ID
            channel: Data channel number
            start_time: Start time relative to DW end (ms)
            duration: Schedule duration (ms)
            peer_id: Peer node ID

        Returns:
            NDPSchedule object
        """
        schedule = NDPSchedule(
            ndp_id=ndp_id,
            channel=channel,
            start_time=start_time,
            duration=duration,
            peer_id=peer_id
        )

        self.outgoing_schedules.append(schedule)

        # Publish event
        self.node.event_bus.publish(
            'ndp_schedule_created',
            ndp_id=ndp_id,
            channel=channel,
            start_time=start_time,
            duration=duration,
            peer_id=peer_id,
            timestamp=self.env.now
        )

        return schedule

    def receive_schedule(self, schedule: NDPSchedule) -> bool:
        """Receive and process schedule from peer.

        Args:
            schedule: NDPSchedule from peer

        Returns:
            True if schedule accepted
        """
        # Check for conflicts
        if self._has_conflict(schedule):
            return False

        self.incoming_schedules.append(schedule)

        # Publish event
        self.node.event_bus.publish(
            'ndp_schedule_received',
            ndp_id=schedule.ndp_id,
            channel=schedule.channel,
            start_time=schedule.start_time,
            duration=schedule.duration,
            peer_id=schedule.peer_id,
            timestamp=self.env.now
        )

        return True

    def _has_conflict(self, new_schedule: NDPSchedule) -> bool:
        """Check if new schedule conflicts with existing schedules.

        Args:
            new_schedule: New schedule to check

        Returns:
            True if conflict detected
        """
        # Check against all existing schedules
        for schedule in self.outgoing_schedules + self.incoming_schedules:
            if schedule.channel != new_schedule.channel:
                continue

            # Check time overlap
            start1 = schedule.start_time
            end1 = schedule.start_time + schedule.duration
            start2 = new_schedule.start_time
            end2 = new_schedule.start_time + new_schedule.duration

            # Check overlap
            if not (end1 <= start2 or end2 <= start1):
                return True  # Overlap detected

        return False

    def get_schedules_for_channel(self, channel: int) -> List[NDPSchedule]:
        """Get all schedules for a specific channel.

        Args:
            channel: Channel number

        Returns:
            List of NDPSchedule objects
        """
        all_schedules = self.outgoing_schedules + self.incoming_schedules
        return [s for s in all_schedules if s.channel == channel]

    def remove_schedule(self, ndp_id: int) -> bool:
        """Remove schedule for specific NDP.

        Args:
            ndp_id: NDP instance ID

        Returns:
            True if schedule removed
        """
        removed = False

        # Remove from outgoing
        self.outgoing_schedules = [
            s for s in self.outgoing_schedules if s.ndp_id != ndp_id
        ]
        removed = True

        # Remove from incoming
        self.incoming_schedules = [
            s for s in self.incoming_schedules if s.ndp_id != ndp_id
        ]
        removed = True

        return removed

    def get_next_schedule(self, current_time: float) -> Optional[NDPSchedule]:
        """Get next upcoming schedule.

        Args:
            current_time: Current simulation time (ms)

        Returns:
            Next NDPSchedule or None
        """
        all_schedules = self.outgoing_schedules + self.incoming_schedules

        # Filter schedules that haven't started yet
        future_schedules = [
            s for s in all_schedules
            if s.start_time > current_time
        ]

        if not future_schedules:
            return None

        # Return earliest schedule
        return min(future_schedules, key=lambda s: s.start_time)
