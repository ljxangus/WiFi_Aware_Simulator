"""Mobility models for NAN nodes."""

import random
import math
from typing import Tuple


class MobilityModel:
    """Base mobility model."""

    def __init__(self, env, config):
        """Initialize mobility model.

        Args:
            env: SimPy environment
            config: Configuration dictionary
        """
        self.env = env
        self.config = config
        self.area_size = config.get('node.area_size', [100, 100])

    def get_position(self) -> Tuple[float, float]:
        """Get current position.

        Returns:
            Position (x, y) in meters
        """
        raise NotImplementedError

    def update_position(self) -> None:
        """Update position based on mobility model."""
        raise NotImplementedError


class StaticMobility(MobilityModel):
    """Static mobility model (no movement)."""

    def __init__(self, env, config, initial_position: Tuple[float, float]):
        """Initialize static mobility.

        Args:
            env: SimPy environment
            config: Configuration dictionary
            initial_position: Initial (x, y) position
        """
        super().__init__(env, config)
        self.position = initial_position

    def get_position(self) -> Tuple[float, float]:
        """Get current position.

        Returns:
            Position (x, y) in meters
        """
        return self.position

    def update_position(self) -> None:
        """No position updates for static model."""
        pass


class RandomWalk(MobilityModel):
    """Random Walk mobility model."""

    def __init__(self, env, config, initial_position: Tuple[float, float]):
        """Initialize random walk mobility.

        Args:
            env: SimPy environment
            config: Configuration dictionary
            initial_position: Initial (x, y) position
        """
        super().__init__(env, config)

        self.position = list(initial_position)
        self.target_position = list(initial_position)

        # Mobility parameters
        self.speed_min = config.get('mobility.speed_min', 0.5)  # m/s
        self.speed_max = config.get('mobility.speed_max', 2.0)  # m/s
        self.pause_time = config.get('mobility.pause_time', 5.0)  # s

        # State
        self.is_paused = False
        self.pause_end_time = 0
        self.last_update_time = env.now
        self.current_speed = random.uniform(self.speed_min, self.speed_max)

        # Pick initial target
        self._pick_new_target()

    def get_position(self) -> Tuple[float, float]:
        """Get current position.

        Returns:
            Position (x, y) in meters
        """
        return tuple(self.position)

    def update_position(self) -> None:
        """Update position based on random walk."""
        # Calculate time delta (seconds)
        delta_time = (self.env.now - self.last_update_time) / 1000

        # Check if paused
        if self.is_paused:
            if self.env.now >= self.pause_end_time:
                self.is_paused = False
                self._pick_new_target()
            self.last_update_time = self.env.now
            return

        # Move towards target
        dx = self.target_position[0] - self.position[0]
        dy = self.target_position[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)

        if distance < 1.0:  # Reached target
            # Start pause
            self.is_paused = True
            self.pause_end_time = self.env.now + (self.pause_time * 1000)
        else:
            # Move towards target
            move_distance = self.current_speed * delta_time

            if move_distance >= distance:
                # Reached target
                self.position = list(self.target_position)
                self.is_paused = True
                self.pause_end_time = self.env.now + (self.pause_time * 1000)
            else:
                # Move step towards target
                step_x = (dx / distance) * move_distance
                step_y = (dy / distance) * move_distance

                self.position[0] += step_x
                self.position[1] += step_y

        self.last_update_time = self.env.now

    def _pick_new_target(self) -> None:
        """Pick new random target position."""
        self.target_position = [
            random.uniform(0, self.area_size[0]),
            random.uniform(0, self.area_size[1])
        ]
        self.current_speed = random.uniform(self.speed_min, self.speed_max)
