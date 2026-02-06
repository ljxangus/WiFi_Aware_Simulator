"""Statistics collection and export for Wi-Fi Aware simulation."""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class StatisticsCollector:
    """Collect and export simulation statistics."""

    def __init__(self, env, output_dir: str):
        """Initialize statistics collector.

        Args:
            env: SimPy environment
            output_dir: Output directory for results
        """
        self.env = env
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Metrics storage
        self.metrics = {
            'discovery_latency': [],
            'discovery_events': [],
            'power_consumption': {},
            'hop_count_distribution': {},
            'cluster_formation_time': None,
            'service_published': [],
            'service_subscribed': [],
            'service_discovered': [],
            'ndp_created': [],
            'beacon_events': [],
            'position_updates': []
        }

    def record_discovery(self, publisher_id: int, subscriber_id: int,
                        service_name: str, latency: float) -> None:
        """Record a service discovery event.

        Args:
            publisher_id: Publisher node ID
            subscriber_id: Subscriber node ID
            service_name: Name of discovered service
            latency: Discovery latency in ms
        """
        self.metrics['discovery_latency'].append({
            'publisher_id': publisher_id,
            'subscriber_id': subscriber_id,
            'service_name': service_name,
            'latency': latency,
            'timestamp': self.env.now
        })

        self.metrics['discovery_events'].append({
            'publisher_id': publisher_id,
            'subscriber_id': subscriber_id,
            'service_name': service_name,
            'timestamp': self.env.now
        })

    def record_power_consumption(self, node_id: int, energy: float,
                                avg_power: float, state_durations: Dict) -> None:
        """Record power consumption for a node.

        Args:
            node_id: Node identifier
            energy: Total energy consumption in mJ
            avg_power: Average power in mW
            state_durations: Time spent in each state (ms)
        """
        self.metrics['power_consumption'][node_id] = {
            'energy_mj': energy,
            'avg_power_mw': avg_power,
            'state_durations': state_durations
        }

    def record_hop_count(self, node_id: int, hop_count: int) -> None:
        """Record hop count to AM for a node.

        Args:
            node_id: Node identifier
            hop_count: Hop count to Anchor Master
        """
        if hop_count not in self.metrics['hop_count_distribution']:
            self.metrics['hop_count_distribution'][hop_count] = 0

        self.metrics['hop_count_distribution'][hop_count] += 1

    def record_cluster_formation(self, time_ms: float) -> None:
        """Record cluster formation time.

        Args:
            time_ms: Time when cluster formed (ms)
        """
        if self.metrics['cluster_formation_time'] is None:
            self.metrics['cluster_formation_time'] = time_ms

    def record_service_published(self, node_id: int, service_id: int,
                                service_name: str) -> None:
        """Record service publication.

        Args:
            node_id: Publisher node ID
            service_id: Service identifier
            service_name: Service name
        """
        self.metrics['service_published'].append({
            'node_id': node_id,
            'service_id': service_id,
            'service_name': service_name,
            'timestamp': self.env.now
        })

    def record_service_subscribed(self, node_id: int, subscribe_id: int,
                                 service_name: str, mode: str) -> None:
        """Record service subscription.

        Args:
            node_id: Subscriber node ID
            subscribe_id: Subscription identifier
            service_name: Service name
            mode: Subscribe mode (active/passive)
        """
        self.metrics['service_subscribed'].append({
            'node_id': node_id,
            'subscribe_id': subscribe_id,
            'service_name': service_name,
            'mode': mode,
            'timestamp': self.env.now
        })

    def record_service_discovered(self, subscriber_id: int, publisher_id: int,
                                 service_name: str, latency: float) -> None:
        """Record service discovery.

        Args:
            subscriber_id: Subscriber node ID
            publisher_id: Publisher node ID
            service_name: Service name
            latency: Discovery latency (ms)
        """
        self.metrics['service_discovered'].append({
            'subscriber_id': subscriber_id,
            'publisher_id': publisher_id,
            'service_name': service_name,
            'latency': latency,
            'timestamp': self.env.now
        })

    def record_ndp_created(self, initiator_id: int, responder_id: int,
                          ndp_id: int) -> None:
        """Record NDP creation.

        Args:
            initiator_id: Initiator node ID
            responder_id: Responder node ID
            ndp_id: NDP instance ID
        """
        self.metrics['ndp_created'].append({
            'initiator_id': initiator_id,
            'responder_id': responder_id,
            'ndp_id': ndp_id,
            'timestamp': self.env.now
        })

    def get_discovery_summary(self) -> Dict[str, Any]:
        """Get summary statistics for discovery.

        Returns:
            Dictionary with discovery statistics
        """
        latencies = [d['latency'] for d in self.metrics['discovery_latency']]

        if not latencies:
            return {
                'total_discoveries': 0,
                'avg_latency': 0,
                'min_latency': 0,
                'max_latency': 0,
                'median_latency': 0
            }

        sorted_latencies = sorted(latencies)

        return {
            'total_discoveries': len(latencies),
            'avg_latency': sum(latencies) / len(latencies),
            'min_latency': min(latencies),
            'max_latency': max(latencies),
            'median_latency': sorted_latencies[len(sorted_latencies) // 2]
        }

    def get_power_summary(self) -> Dict[str, Any]:
        """Get summary statistics for power consumption.

        Returns:
            Dictionary with power statistics
        """
        if not self.metrics['power_consumption']:
            return {
                'total_energy_mj': 0,
                'avg_power_mw': 0,
                'node_count': 0
            }

        total_energy = sum(
            p['energy_mj'] for p in self.metrics['power_consumption'].values()
        )
        avg_powers = [
            p['avg_power_mw'] for p in self.metrics['power_consumption'].values()
        ]

        return {
            'total_energy_mj': total_energy,
            'avg_power_mw': sum(avg_powers) / len(avg_powers),
            'min_power_mw': min(avg_powers),
            'max_power_mw': max(avg_powers),
            'node_count': len(self.metrics['power_consumption'])
        }

    def export_results(self, filename_prefix: str = "simulation") -> None:
        """Export all results to CSV and JSON files.

        Args:
            filename_prefix: Prefix for output files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{filename_prefix}_{timestamp}"

        # Export discovery latency
        self._export_csv(
            f"{base_name}_discovery_latency.csv",
            self.metrics['discovery_latency']
        )

        # Export power consumption
        self._export_power_csv(f"{base_name}_power.csv")

        # Export service discovery events
        self._export_csv(
            f"{base_name}_service_discovery.csv",
            self.metrics['service_discovered']
        )

        # Export summary JSON
        self._export_json(f"{base_name}_summary.json")

    def _export_csv(self, filename: str, data: List[Dict]) -> None:
        """Export data to CSV file.

        Args:
            filename: Output filename
            data: List of dictionaries to export
        """
        if not data:
            return

        filepath = self.output_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def _export_power_csv(self, filename: str) -> None:
        """Export power consumption to CSV file.

        Args:
            filename: Output filename
        """
        filepath = self.output_dir / filename

        with open(filepath, 'w', newline='') as f:
            fieldnames = ['node_id', 'energy_mj', 'avg_power_mw',
                         'sleep_time', 'listen_time', 'rx_time', 'tx_time']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for node_id, power_data in self.metrics['power_consumption'].items():
                state_durations = power_data['state_durations']

                writer.writerow({
                    'node_id': node_id,
                    'energy_mj': f"{power_data['energy_mj']:.2f}",
                    'avg_power_mw': f"{power_data['avg_power_mw']:.2f}",
                    'sleep_time': f"{state_durations.get('sleep', 0):.2f}",
                    'listen_time': f"{state_durations.get('listen', 0):.2f}",
                    'rx_time': f"{state_durations.get('rx', 0):.2f}",
                    'tx_time': f"{state_durations.get('tx', 0):.2f}"
                })

    def _export_json(self, filename: str) -> None:
        """Export summary statistics to JSON file.

        Args:
            filename: Output filename
        """
        filepath = self.output_dir / filename

        summary = {
            'simulation_duration_ms': self.env.now,
            'cluster_formation_time_ms': self.metrics['cluster_formation_time'],
            'discovery_summary': self.get_discovery_summary(),
            'power_summary': self.get_power_summary(),
            'hop_count_distribution': self.metrics['hop_count_distribution'],
            'total_services_published': len(self.metrics['service_published']),
            'total_services_subscribed': len(self.metrics['service_subscribed']),
            'total_services_discovered': len(self.metrics['service_discovered']),
            'total_ndp_instances': len(self.metrics['ndp_created'])
        }

        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
