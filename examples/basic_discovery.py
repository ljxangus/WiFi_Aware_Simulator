"""Basic service discovery example for Wi-Fi Aware Simulator."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.simulation import Simulation


def run_basic_discovery():
    """Run basic service discovery simulation."""
    print("=" * 60)
    print("Wi-Fi Aware Simulator - Basic Discovery Example")
    print("=" * 60)
    print()

    # Create and run simulation with default config
    sim = Simulation()

    # Run for 30 seconds (30000 ms)
    sim.run(duration=30000)

    print()
    print("Simulation completed! Check the 'output' directory for results.")


if __name__ == '__main__':
    run_basic_discovery()
