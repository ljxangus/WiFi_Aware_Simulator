"""Discovery Window scheduler for NAN."""

import random
from typing import Optional, List


class DiscoveryWindow:
    """Discovery Window (DW) scheduler per 802.11 Annex AQ."""

    def __init__(self, env, node, config, channel):
        """Initialize Discovery Window scheduler.

        Args:
            env: SimPy environment
            node: NANNode instance
            config: Configuration dictionary
            channel: ChannelModel instance
        """
        self.env = env
        self.node = node
        self.config = config
        self.channel = channel

        # Timing parameters
        self.dw_interval = config.get('time.dw_interval', 512)  # ms
        self.dw_duration = config.get('time.dw_duration', 16)  # ms

        # State
        self.dw_active = False
        self.dw_count = 0
        self.last_dw_time = 0
        self.current_channel = 6  # Start on social channel 6

    def time_to_next_dw(self) -> float:
        """Calculate time until next DW.

        Returns:
            Time in milliseconds
        """
        elapsed = self.env.now - self.last_dw_time
        return max(0, self.dw_interval - elapsed)

    def is_dw_active(self) -> bool:
        """Check if currently in Discovery Window.

        Returns:
            True if DW is active
        """
        return self.dw_active

    def run(self):
        """Main DW scheduling loop."""
        while True:
            # Wait for next DW
            yield self.env.timeout(self.time_to_next_dw())

            # Start DW
            self.dw_active = True
            self.dw_count += 1
            self.last_dw_time = self.env.now

            # Switch to social channel
            self._switch_to_social_channel()

            # Set power state to listen
            from phy_mac.power_state import PowerState
            self.node.power_state.set_state(PowerState.LISTEN)

            # Process DW
            yield self.env.process(self._process_dw())

            # End DW
            self.dw_active = False

            # Return to data channel or sleep
            from phy_mac.power_state import PowerState
            self.node.power_state.set_state(PowerState.SLEEP)

    def _switch_to_social_channel(self) -> None:
        """Switch to social channel for DW."""
        social_channels = self.config.get('channel.social_channel', [6, 149])
        # Alternate between social channels
        self.current_channel = social_channels[self.dw_count % len(social_channels)]

    def _process_dw(self):
        """Process Discovery Window activities.

        During DW:
        1. Send/receive Beacons
        2. Send/receive SDF frames
        3. Handle service matching
        """
        # Send beacon if we're a master
        if self.node.role_state.is_master():
            yield self.env.process(self._send_beacon())

        # Listen for beacons (all nodes)
        yield self.env.process(self._receive_beacons())

        # Process Service Discovery Frames
        yield self.env.process(self._process_sdf_frames())

        # Wait for DW to end
        yield self.env.timeout(self.dw_duration)

    def _send_beacon(self):
        """Send NAN beacon frame."""
        # Check medium and backoff
        if self.channel.is_idle():
            backoff = self.channel.csma_ca_backoff()
            yield self.env.timeout(backoff)

            if self.channel.is_idle():
                # Send beacon
                from phy_mac.power_state import PowerState
                self.node.power_state.set_state(PowerState.TX)

                beacon = self._create_beacon()
                duration = 0.5  # ms (typical beacon duration)

                self.channel.start_transmission(self.node.node_id, duration)
                yield self.env.timeout(duration)
                self.channel.end_transmission(self.node.node_id)

                # Publish beacon event
                self.node.event_bus.publish(
                    'beacon_sent',
                    node_id=self.node.node_id,
                    timestamp=self.env.now
                )

    def _create_beacon(self):
        """Create beacon frame for transmission."""
        from phy_mac.frame import NANBeaconFrame

        beacon = NANBeaconFrame(
            timestamp=self.node.tsf_clock.get_time(),
            beacon_interval=100,
            cluster_id=self.node.cluster.cluster_id_beacon if self.node.cluster else 0,
            am_rank=self.node.role_state.rank,
            hop_count=self.node.role_state.hop_count_to_am,
            source_addr=self.node.node_id,
            supported_channels=[self.current_channel]
        )
        return beacon

    def _receive_beacons(self):
        """Receive and process beacon frames."""
        from phy_mac.power_state import PowerState
        self.node.power_state.set_state(PowerState.RX)

        # Listen for beacons (simplified - in reality would handle actual frames)
        yield self.env.timeout(1)  # ms

        # Process beacon reception would happen here
        self.node.event_bus.publish(
            'beacon_received',
            node_id=self.node.node_id,
            timestamp=self.env.now
        )

    def _process_sdf_frames(self):
        """Process Service Discovery Frames (send/receive)."""
        # Send SDF if we have published services
        if hasattr(self.node, 'publisher') and self.node.publisher.has_active_services():
            yield self.env.process(self._send_sdf())

        # Receive SDF
        yield self.env.process(self._receive_sdf())

    def _send_sdf(self):
        """Send Service Discovery Frame."""
        if not self.channel.is_idle():
            return

        backoff = self.channel.csma_ca_backoff()
        yield self.env.timeout(backoff)

        if self.channel.is_idle():
            from phy_mac.power_state import PowerState
            self.node.power_state.set_state(PowerState.TX)

            duration = 1.0  # ms
            self.channel.start_transmission(self.node.node_id, duration)
            yield self.env.timeout(duration)
            self.channel.end_transmission(self.node.node_id)

            self.node.event_bus.publish(
                'sdf_sent',
                node_id=self.node.node_id,
                timestamp=self.env.now
            )

    def _receive_sdf(self):
        """Receive Service Discovery Frame."""
        from phy_mac.power_state import PowerState
        self.node.power_state.set_state(PowerState.RX)
        yield self.env.timeout(2)  # ms (listen for SDF frames)
