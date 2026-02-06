"""TSF Clock synchronization for NAN devices."""

import random
from typing import Optional


class TSFClock:
    """Timing Synchronization Function clock per 802.11 standard."""

    def __init__(self, env, drift_ppm: int = 0):
        """Initialize TSF clock.

        Args:
            env: SimPy environment
            drift_ppm: Clock drift in parts-per-million
        """
        self.env = env
        self.tsf = 0  # 64-bit TSF timer (us)
        self.drift_ppm = drift_ppm
        self.base_time = env.now  # Reference time (ms)
        self.sync_count = 0  # Number of synchronizations performed

    def get_time(self) -> int:
        """Get current TSF time with drift applied.

        Returns:
            TSF timestamp in microseconds
        """
        # Convert elapsed simulation time to microseconds
        elapsed_us = (self.env.now - self.base_time) * 1000

        # Apply clock drift
        drift_factor = 1 + (self.drift_ppm / 1e6)

        return int(self.tsf + elapsed_us * drift_factor)

    def synchronize(self, beacon_tsf: int, rtt_error: int = 0) -> None:
        """Synchronize TSF to received beacon timestamp.

        Args:
            beacon_tsf: TSF value from received beacon
            rtt_error: Round-trip time error estimate (us)
        """
        current = self.get_time()
        offset = beacon_tsf - current + rtt_error

        # Apply offset to base TSF
        self.tsf += offset
        self.base_time = self.env.now
        self.sync_count += 1

    def get_drift_error(self) -> float:
        """Get current drift error in microseconds.

        Returns:
            Drift error in us
        """
        elapsed_us = (self.env.now - self.base_time) * 1000
        return elapsed_us * (self.drift_ppm / 1e6)

    def reset(self) -> None:
        """Reset TSF timer to zero."""
        self.tsf = 0
        self.base_time = self.env.now
        self.sync_count = 0
