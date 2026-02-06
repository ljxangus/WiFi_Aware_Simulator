"""Power state machine for energy consumption tracking."""

from typing import List, Tuple
from enum import Enum


class PowerState(Enum):
    """Power consumption states."""
    SLEEP = "sleep"
    LISTEN = "listen"
    RX = "rx"
    TX = "tx"


class PowerStateMachine:
    """Power state machine tracking energy consumption."""

    # Default power consumption values (mW)
    DEFAULT_POWER = {
        PowerState.SLEEP: 1,
        PowerState.LISTEN: 200,
        PowerState.RX: 300,
        PowerState.TX: 800
    }

    def __init__(self, env, config):
        """Initialize power state machine.

        Args:
            env: SimPy environment
            config: Configuration dictionary
        """
        self.env = env
        self.config = config

        # Load power values from config or use defaults
        self.power_values = {
            PowerState.SLEEP: config.get('power.sleep', self.DEFAULT_POWER[PowerState.SLEEP]),
            PowerState.LISTEN: config.get('power.listen', self.DEFAULT_POWER[PowerState.LISTEN]),
            PowerState.RX: config.get('power.rx', self.DEFAULT_POWER[PowerState.RX]),
            PowerState.TX: config.get('power.tx', self.DEFAULT_POWER[PowerState.TX])
        }

        # State tracking
        self.current_state = PowerState.SLEEP
        self.last_change_time = env.now
        self.state_history: List[Tuple[float, PowerState]] = [(env.now, PowerState.SLEEP)]
        self.total_energy = 0.0  # mJ

    def set_state(self, new_state: PowerState) -> None:
        """Transition to new power state.

        Args:
            new_state: New power state
        """
        if self.current_state == new_state:
            return

        # Calculate energy consumption in current state
        duration = self.env.now - self.last_change_time  # ms
        power = self.power_values[self.current_state]  # mW
        energy = power * duration / 1000  # mJ (mW * ms / 1000)

        self.total_energy += energy

        # Update state
        self.current_state = new_state
        self.last_change_time = self.env.now
        self.state_history.append((self.env.now, new_state))

    def get_state(self) -> PowerState:
        """Get current power state.

        Returns:
            Current power state
        """
        return self.current_state

    def get_energy_consumption(self) -> float:
        """Get total energy consumption.

        Returns:
            Total energy in mJ
        """
        # Add energy for current state
        duration = self.env.now - self.last_change_time
        power = self.power_values[self.current_state]
        current_energy = power * duration / 1000

        return self.total_energy + current_energy

    def get_average_power(self) -> float:
        """Get average power consumption.

        Returns:
            Average power in mW
        """
        total_energy = self.get_energy_consumption()
        total_time = self.env.now  # ms

        if total_time == 0:
            return 0

        return total_energy * 1000 / total_time  # mW

    def get_state_durations(self) -> dict:
        """Get time spent in each state.

        Returns:
            Dictionary mapping state to duration (ms)
        """
        durations = {state: 0.0 for state in PowerState}

        for i in range(len(self.state_history) - 1):
            time1, state1 = self.state_history[i]
            time2, state2 = self.state_history[i + 1]
            duration = time2 - time1
            durations[state1] += duration

        # Add current state duration
        duration = self.env.now - self.state_history[-1][0]
        durations[self.current_state] += duration

        return {state.name: durations[state] for state in PowerState}
