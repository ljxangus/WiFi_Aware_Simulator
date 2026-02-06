# Wi-Fi Aware (NAN) Protocol Simulator

A high-fidelity simulator for Wi-Fi Neighbor Awareness Networking (NAN) protocol based on SimPy, supporting IEEE 802.11-2016 Annex AQ and WFA NAN 3.1/4.0 specifications.

## Features

- **Protocol Compliance**: Implements NAN Cluster formation, Discovery Windows, and Service Discovery
- **TSF Synchronization**: Timing Synchronization Function with clock drift modeling
- **Service Discovery**: Publish/Subscribe state machines with match filtering
- **NDP Support**: NAN Data Interface for data path establishment
- **Mobility Models**: Static and Random Walk mobility
- **Energy Modeling**: Detailed power consumption tracking (Sleep/Listen/RX/TX states)
- **Channel Modeling**: Log-distance path loss with CSMA/CA
- **Statistics**: Comprehensive metrics collection and CSV/JSON export

## Project Structure

```
WiFi_Aware_Simulator/
├── config/                 # Configuration files
│   ├── default.yaml        # Default simulation parameters
│   └── scenarios/          # Scenario presets
├── src/                    # Source code
│   ├── core/              # Core simulation engine
│   ├── nan/               # NAN protocol (Cluster, TSF, Roles)
│   ├── discovery/         # Service Discovery (DW, Publish/Subscribe)
│   ├── phy_mac/           # PHY/MAC layer (Channel, Frames, Power)
│   ├── ndp/               # Data Path (NDI, Schedule)
│   ├── node/              # Node implementation
│   └── utils/             # Statistics and logging
├── examples/              # Example scripts
├── tests/                 # Unit tests
└── output/                # Simulation results
```

## Installation

### Requirements

- Python 3.10+
- SimPy 4.0+
- PyYAML, NumPy, Pandas

### Setup

#### Option 1: Using Virtual Environment (Recommended)

```bash
# Clone repository
git clone https://github.com/ljxangus/WiFi_Aware_Simulator.git
cd WiFi_Aware_Simulator

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package (optional)
pip install -e .
```

#### Option 2: Using System Python

```bash
# Clone repository
git clone https://github.com/ljxangus/WiFi_Aware_Simulator.git
cd WiFi_Aware_Simulator

# Install dependencies
pip install -r requirements.txt

# Install package (optional)
pip install -e .
```

#### Verify Installation

```bash
# Run tests to verify installation
pytest tests/ -v

# Run basic example
python examples/basic_discovery.py
```

## Quick Start

> **Note**: If you're using a virtual environment, make sure to activate it first:
> ```bash
> source venv/bin/activate  # macOS/Linux
> venv\Scripts\activate     # Windows
> ```

### Basic Discovery Example

```python
from src.core.simulation import Simulation

# Create simulation with default config
sim = Simulation()

# Run for 30 seconds
sim.run(duration=30000)

# Results exported to output/ directory
```

### Using Custom Configuration

```yaml
# config/my_scenario.yaml
node:
  count: 50
  area_size: [200, 200]

time:
  dw_interval: 512
  dw_duration: 16

simulation:
  duration: 60000
  seed: 123
```

```python
sim = Simulation(config_path='config/my_scenario.yaml')
sim.run()
```

### Command Line

```bash
# First, activate virtual environment if using one:
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate     # Windows

# Run with default config
python -m src.core.simulation

# Run with custom config
python -m src.core.simulation config/scenarios/high_density.yaml

# Run basic discovery example
python examples/basic_discovery.py

# Run NDP data path example
python examples/ndp_example.py
```

## Configuration

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `node.count` | Number of nodes | 20 |
| `time.dw_interval` | Discovery Window interval (ms) | 512 |
| `time.dw_duration` | Discovery Window duration (ms) | 16 |
| `mobility.enabled` | Enable mobility | true |
| `mobility.model` | Mobility model (random_walk/static) | random_walk |
| `simulation.duration` | Simulation duration (ms) | 60000 |
| `simulation.seed` | Random seed | 42 |

### Power States

- **Sleep**: 1 mW (default)
- **Listen**: 200 mW (default)
- **RX**: 300 mW (default)
- **TX**: 800 mW (default)

## Output

### CSV Files

- `simulation_*_discovery_latency.csv` - Per-discovery latency
- `simulation_*_power.csv` - Per-node energy consumption
- `simulation_*_service_discovery.csv` - Service discovery events

### JSON Summary

- `simulation_*_summary.json` - Aggregated statistics

### Key Metrics

- **Discovery Latency**: Time from subscription to discovery
- **Energy Consumption**: Total and per-state energy usage
- **Hop Count Distribution**: Distance to Anchor Master
- **Success Rate**: Percentage of services discovered

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_cluster.py -v

# Run with coverage
pytest --cov=src tests/
```

## Architecture

### NAN Cluster

```
┌─────────────────────────────────────┐
│         NAN Cluster                  │
│  ┌─────────────────────────────┐    │
│  │  Anchor Master (AM)         │    │
│  │  - Highest priority         │    │
│  │  - Sends beacons            │    │
│  └─────────────────────────────┘    │
│           ↑                           │
│  ┌────────┴────────┐                 │
│  │  NMS (1 hop)    │                 │
│  │  - Forwards     │                 │
│  │    beacons      │                 │
│  └─────────────────┘                 │
│           ↑                           │
│  ┌────────┴────────┐                 │
│  │  NMNS (2+ hops) │                 │
│  │  - Regular      │                 │
│  │    devices      │                 │
│  └─────────────────┘                 │
└─────────────────────────────────────┘
```

### Discovery Window Timing

```
Time ──────────────────────────────────────────────→

┌────────┐     ┌────────┐     ┌────────┐
│   DW   │     │   DW   │     │   DW   │
│  16ms  │     │  16ms  │     │  16ms  │
└────────┘     └────────┘     └────────┘
   512ms         512ms         512ms

Social Channel 6      Social Channel 149
(Beacon + SDF)        (Beacon + SDF)
```

## Performance

### Scalability

- **Small**: 10 nodes, 30s sim time ~ 5s runtime
- **Medium**: 50 nodes, 60s sim time ~ 30s runtime
- **Large**: 100+ nodes (requires optimization)

### Memory

- Base: ~50 MB
- Per node: ~2 MB
- 50 nodes: ~150 MB

## Standards Compliance

- **IEEE 802.11-2016 Annex AQ**: NAN protocol fundamentals
- **WFA NAN Specification 3.1**: Service discovery
- **WFA NAN Specification 4.0**: NDP data path

## Limitations

- Simplified collision detection (no capture effect)
- Basic routing (hop count estimation)
- No security/encryption
- Single social channel per DW

## Future Work

- [ ] Multi-cluster synchronization
- [ ] Advanced mobility models (RWP, Gauss-Markov)
- [ ] NDP data transfer simulation
- [ ] Real-time visualization
- [ ] Network layer integration

## Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## License

MIT License - See LICENSE file for details

## References

- IEEE 802.11-2016 Standard, Annex AQ
- Wi-Fi Alliance NAN Specification v3.1
- Wi-Fi Alliance NAN Specification v4.0

## Citation

If you use this simulator in research, please cite:

```bibtex
@software{wifi_aware_simulator,
  title={Wi-Fi Aware (NAN) Protocol Simulator},
  author={Jiaxin Liang},
  year={2026},
  url={https://github.com/ljxangus/WiFi_Aware_Simulator}
}
```

## Contact

For questions, issues, or contributions, please open a GitHub issue.
