"""NAN Node - Main node class for Wi-Fi Aware simulation."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
from typing import List, Tuple, Optional, Dict
from phy_mac.power_state import PowerStateMachine, PowerState
from phy_mac.channel import ChannelModel
from nan.tsf import TSFClock
from nan.roles import RoleState, NANRole
from nan.cluster import Cluster
from discovery.discovery_window import DiscoveryWindow
from discovery.publish import PublishStateMachine
from discovery.subscribe import SubscribeStateMachine
from ndp.ndi import NANDataInterface
from ndp.schedule import NDPScheduleNegotiator
from node.mobility import MobilityModel, StaticMobility, RandomWalk
from core.event_bus import EventBus


class NANNode:
    """NAN Node implementing Wi-Fi Aware protocol."""

    def __init__(self, env, node_id: int, config, position: Tuple[float, float],
                 event_bus: EventBus, channel: ChannelModel):
        """Initialize NAN node.

        Args:
            env: SimPy environment
            node_id: Unique node identifier
            config: Configuration dictionary
            position: Initial (x, y) position in meters
            event_bus: Event bus for publishing events
            channel: Shared channel model
        """
        self.env = env
        self.node_id = node_id
        self.config = config
        self.position = position
        self.event_bus = event_bus
        self.channel = channel

        # Node parameters
        self.tx_power = config.get('node.tx_power', 20)  # dBm
        self.rx_sensitivity = config.get('node.rx_sensitivity', -85)  # dBm

        # Initialize sub-modules
        self.tsf_clock = TSFClock(
            env,
            drift_ppm=random.randint(0, config.get('node.clock_drift_max', 50))
        )
        self.power_state = PowerStateMachine(env, config)
        self.role_state = RoleState()
        self.role_state.rank = random.randint(0, 254)

        # Cluster membership
        self.cluster: Optional[Cluster] = None

        # Discovery
        self.discovery_window = DiscoveryWindow(env, self, config, channel)
        self.publisher = PublishStateMachine(env, self, config)
        self.subscriber = SubscribeStateMachine(env, self, config)

        # NDP
        self.ndi = NANDataInterface(env, self, config)
        self.ndp_schedule = NDPScheduleNegotiator(env, self, config)

        # Mobility
        mobility_enabled = config.get('mobility.enabled', True)
        if mobility_enabled and config.get('mobility.model', 'random_walk') == 'random_walk':
            self.mobility = RandomWalk(env, config, position)
        else:
            self.mobility = StaticMobility(env, config, position)

    def run(self):
        """Main node process."""
        # Start all sub-processes
        processes = [
            self.env.process(self.discovery_window.run()),
            self.env.process(self.publisher.run()),
            self.env.process(self.subscriber.run()),
            self.env.process(self._mobility_loop()),
            self.env.process(self._power_tracking_loop())
        ]

        # Wait for all processes
        yield from processes

    def _mobility_loop(self):
        """Update node mobility."""
        while True:
            self.mobility.update_position()
            self.position = self.mobility.get_position()

            # Publish position update
            self.event_bus.publish(
                'position_update',
                node_id=self.node_id,
                position=self.position,
                timestamp=self.env.now
            )

            # Update every 100ms
            yield self.env.timeout(100)

    def _power_tracking_loop(self):
        """Track power consumption periodically."""
        while True:
            # Publish power state
            self.event_bus.publish(
                'power_update',
                node_id=self.node_id,
                state=self.power_state.get_state().value,
                energy=self.power_state.get_energy_consumption(),
                avg_power=self.power_state.get_average_power(),
                timestamp=self.env.now
            )

            # Update every second
            yield self.env.timeout(1000)

    def can_communicate_with(self, other_node) -> bool:
        """Check if can communicate with another node.

        Args:
            other_node: Other NANNode

        Returns:
            True if communication is possible
        """
        rssi = self.channel.calculate_rssi(
            other_node.tx_power,
            other_node.position,
            self.position
        )

        return rssi >= self.rx_sensitivity

    def synchronize_to_beacon(self, beacon_tsf: int, hop_count: int) -> None:
        """Synchronize to received beacon.

        Args:
            beacon_tsf: TSF timestamp from beacon
            hop_count: Hop count from AM
        """
        # Estimate RTT error based on hop count
        rtt_error = hop_count * 10  # 10 us per hop (simplified)

        self.tsf_clock.synchronize(beacon_tsf, rtt_error)

        # Update hop count
        self.role_state.hop_count_to_am = hop_count

    def get_rssi_to(self, other_node) -> float:
        """Get RSSI to another node.

        Args:
            other_node: Other NANNode

        Returns:
            RSSI in dBm
        """
        return self.channel.calculate_rssi(
            self.tx_power,
            self.position,
            other_node.position
        )
