"""NDP (Data Path) example for Wi-Fi Aware Simulator."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.simulation import Simulation
from core.config import Config


def run_ndp_example():
    """Run NDP data path simulation."""
    print("=" * 60)
    print("Wi-Fi Aware Simulator - NDP Data Path Example")
    print("=" * 60)
    print()

    # Create simulation
    sim = Simulation()

    # Run for 60 seconds (60000 ms)
    sim.run(duration=60000)

    print()
    print("Simulation completed! Check the 'output' directory for results.")
    print("NDP instances and schedules are tracked in the summary.")


if __name__ == '__main__':
    run_ndp_example()
