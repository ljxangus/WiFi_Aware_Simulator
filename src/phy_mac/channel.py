"""PHY/MAC channel model with path loss and CSMA/CA."""

import math
import random
from typing import List, Optional, Tuple


class ChannelModel:
    """Wireless channel model with path loss and CSMA/CA."""

    def __init__(self, env, config):
        """Initialize channel model.

        Args:
            env: SimPy environment
            config: Configuration dictionary
        """
        self.env = env
        self.config = config
        self.medium_busy = False
        self.current_transmissions = []  # Track ongoing transmissions

        # Channel parameters
        self.path_loss_exponent = config.get('channel.path_loss_exponent', 3.5)
        self.ref_distance = config.get('channel.reference_distance', 1.0)
        self.ref_loss = config.get('channel.reference_loss', 40.0)

        # MAC parameters
        self.slot_time = config.get('mac.slot_time', 9)  # us
        self.cw_min = config.get('mac.cw_min', 15)
        self.cw_max = config.get('mac.cw_max', 1023)

    def calculate_distance(self, pos1: Tuple[float, float],
                          pos2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two positions.

        Args:
            pos1: First position (x, y) in meters
            pos2: Second position (x, y) in meters

        Returns:
            Distance in meters
        """
        x1, y1 = pos1
        x2, y2 = pos2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def calculate_path_loss(self, distance: float) -> float:
        """Calculate path loss using log-distance model.

        Args:
            distance: Distance in meters

        Returns:
            Path loss in dB
        """
        if distance < self.ref_distance:
            distance = self.ref_distance

        path_loss = (
            self.ref_loss +
            10 * self.path_loss_exponent * math.log10(distance / self.ref_distance)
        )
        return path_loss

    def calculate_rssi(self, tx_power: float, tx_pos: Tuple[float, float],
                      rx_pos: Tuple[float, float]) -> float:
        """Calculate received signal strength.

        Args:
            tx_power: Transmit power in dBm
            tx_pos: Transmitter position (x, y) in meters
            rx_pos: Receiver position (x, y) in meters

        Returns:
            RSSI in dBm
        """
        distance = self.calculate_distance(tx_pos, rx_pos)
        path_loss = self.calculate_path_loss(distance)
        rssi = tx_power - path_loss

        # Add small random variation (shadowing)
        rssi += random.gauss(0, 2)  # 2 dB standard deviation

        return rssi

    def can_receive(self, tx_power: float, tx_pos: Tuple[float, float],
                    rx_pos: Tuple[float, float], rx_sensitivity: float) -> bool:
        """Check if receiver can detect the signal.

        Args:
            tx_power: Transmit power in dBm
            tx_pos: Transmitter position
            rx_pos: Receiver position
            rx_sensitivity: Receiver sensitivity in dBm

        Returns:
            True if signal is detectable
        """
        rssi = self.calculate_rssi(tx_power, tx_pos, rx_pos)
        return rssi >= rx_sensitivity

    def is_idle(self) -> bool:
        """Check if medium is idle.

        Returns:
            True if medium is not busy
        """
        # Remove completed transmissions
        self.current_transmissions = [
            t for t in self.current_transmissions
            if t['end_time'] > self.env.now
        ]

        self.medium_busy = len(self.current_transmissions) > 0
        return not self.medium_busy

    def csma_ca_backoff(self) -> float:
        """Calculate CSMA/CA backoff time.

        Returns:
            Backoff time in milliseconds
        """
        cw = self.cw_min
        backoff_slots = random.randint(0, cw)
        backoff_time_us = backoff_slots * self.slot_time
        return backoff_time_us / 1000  # Convert to ms

    def start_transmission(self, source_id: int, duration: float) -> None:
        """Mark medium as busy for transmission.

        Args:
            source_id: ID of transmitting node
            duration: Transmission duration in ms
        """
        self.current_transmissions.append({
            'source_id': source_id,
            'start_time': self.env.now,
            'end_time': self.env.now + duration
        })
        self.medium_busy = True

    def end_transmission(self, source_id: int) -> None:
        """Mark transmission as complete.

        Args:
            source_id: ID of transmitting node
        """
        self.current_transmissions = [
            t for t in self.current_transmissions
            if t['source_id'] != source_id
        ]
