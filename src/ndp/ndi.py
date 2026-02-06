"""NAN Data Interface (NDI) for data path establishment."""

from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class NDPInstance:
    """NDP Instance representing a data path."""
    ndp_id: int
    peer_id: int
    role: str  # 'initiator' or 'responder'
    channel: int
    start_time: float
    duration: int
    state: str = "pending"  # pending, active, terminated


class NANDataInterface:
    """NAN Data Interface for NDP management per WFA NAN 3.1 spec."""

    def __init__(self, env, node, config):
        """Initialize NDI.

        Args:
            env: SimPy environment
            node: NANNode instance
            config: Configuration dictionary
        """
        self.env = env
        self.node = node
        self.config = config

        self.ndp_instances: List[NDPInstance] = []
        self.ndp_id_counter = 0
        self.data_channels = config.get('channel.data_channel', [36, 40, 44, 48])

    def create_ndp(self, peer_id: int, role: str = 'initiator') -> int:
        """Create a new NDP instance.

        Args:
            peer_id: Peer node ID
            role: Role ('initiator' or 'responder')

        Returns:
            NDP ID
        """
        ndp_id = self.ndp_id_counter
        self.ndp_id_counter += 1

        # Select data channel
        channel = self._select_data_channel()

        ndp = NDPInstance(
            ndp_id=ndp_id,
            peer_id=peer_id,
            role=role,
            channel=channel,
            start_time=0,  # Will be set after negotiation
            duration=0,    # Will be set after negotiation
            state='pending'
        )

        self.ndp_instances.append(ndp)

        # Publish event
        self.node.event_bus.publish(
            'ndp_created',
            initiator_id=self.node.node_id if role == 'initiator' else peer_id,
            responder_id=peer_id if role == 'initiator' else self.node.node_id,
            ndp_id=ndp_id,
            timestamp=self.env.now
        )

        return ndp_id

    def terminate_ndp(self, ndp_id: int) -> bool:
        """Terminate an NDP instance.

        Args:
            ndp_id: NDP ID to terminate

        Returns:
            True if terminated successfully
        """
        for ndp in self.ndp_instances:
            if ndp.ndp_id == ndp_id:
                ndp.state = 'terminated'

                self.node.event_bus.publish(
                    'ndp_terminated',
                    ndp_id=ndp_id,
                    timestamp=self.env.now
                )

                return True

        return False

    def get_active_ndps(self) -> List[NDPInstance]:
        """Get all active NDP instances.

        Returns:
            List of active NDP instances
        """
        return [ndp for ndp in self.ndp_instances if ndp.state == 'active']

    def get_ndp_by_peer(self, peer_id: int) -> Optional[NDPInstance]:
        """Get NDP instance with specific peer.

        Args:
            peer_id: Peer node ID

        Returns:
            NDPInstance if found, None otherwise
        """
        for ndp in self.ndp_instances:
            if ndp.peer_id == peer_id and ndp.state == 'active':
                return ndp
        return None

    def _select_data_channel(self) -> int:
        """Select a data channel from available channels.

        Returns:
            Channel number
        """
        import random
        return random.choice(self.data_channels)

    def update_ndp_schedule(self, ndp_id: int, start_time: float, duration: int) -> bool:
        """Update NDP schedule after negotiation.

        Args:
            ndp_id: NDP ID
            start_time: Start time (ms from DW end)
            duration: Duration (ms)

        Returns:
            True if updated successfully
        """
        for ndp in self.ndp_instances:
            if ndp.ndp_id == ndp_id:
                ndp.start_time = start_time
                ndp.duration = duration
                ndp.state = 'active'
                return True

        return False
