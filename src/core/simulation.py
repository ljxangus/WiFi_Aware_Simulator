"""Main simulation engine for Wi-Fi Aware Simulator."""

import simpy
import random
from typing import List
from pathlib import Path

from .config import Config
from .event_bus import EventBus
from nan.cluster import Cluster
from node.nan_node import NANNode
from phy_mac.channel import ChannelModel
from utils.statistics import StatisticsCollector
from utils.logger import SimulationLogger


class Simulation:
    """Main simulation engine for Wi-Fi Aware protocol."""

    def __init__(self, config_path: str = None):
        """Initialize simulation.

        Args:
            config_path: Path to configuration file (optional)
        """
        # Load configuration
        self.config = Config(config_path)

        # Setup random seed
        self.seed = self.config.get('simulation.seed', 42)
        random.seed(self.seed)

        # Create SimPy environment
        self.env = simpy.Environment()

        # Create event bus
        self.event_bus = EventBus()

        # Create logger
        output_dir = self.config.get('simulation.output_dir', 'output')
        self.logger = SimulationLogger(log_dir=output_dir)

        # Create statistics collector
        self.stats = StatisticsCollector(self.env, output_dir)

        # Create channel model
        self.channel = ChannelModel(self.env, self.config)

        # Create nodes
        self.nodes: List[NANNode] = []
        self.clusters: List[Cluster] = []

        # Setup event subscriptions
        self._setup_event_subscriptions()

        self.logger.info(f"Simulation initialized with seed {self.seed}")

    def _setup_event_subscriptions(self) -> None:
        """Setup event bus subscriptions for statistics."""
        self.event_bus.subscribe('service_discovered', self._on_discovery)
        self.event_bus.subscribe('power_update', self._on_power_update)
        self.event_bus.subscribe('service_published', self._on_service_published)
        self.event_bus.subscribe('service_subscribed', self._on_service_subscribed)
        self.event_bus.subscribe('cluster_formed', self._on_cluster_formed)

    def _on_discovery(self, subscriber_id: int, publisher_id: int,
                     service_name: str, latency: float, **kwargs) -> None:
        """Handle service discovery event.

        Args:
            subscriber_id: Subscriber node ID
            publisher_id: Publisher node ID
            service_name: Name of discovered service
            latency: Discovery latency in ms
        """
        self.stats.record_discovery(publisher_id, subscriber_id, service_name, latency)
        self.logger.log_discovery(subscriber_id, publisher_id, service_name, latency)

        # Update subscriber's discovery list
        subscriber = self.get_node_by_id(subscriber_id)
        if subscriber:
            subscriber.subscriber.process_discovery(
                publisher_id, service_name, b"", latency
            )

    def _on_power_update(self, node_id: int, energy: float,
                        avg_power: float, **kwargs) -> None:
        """Handle power update event.

        Args:
            node_id: Node identifier
            energy: Total energy consumption in mJ
            avg_power: Average power in mW
        """
        node = self.get_node_by_id(node_id)
        if node:
            state_durations = node.power_state.get_state_durations()
            self.stats.record_power_consumption(node_id, energy, avg_power, state_durations)

    def _on_service_published(self, node_id: int, service_id: int,
                             service_name: str, **kwargs) -> None:
        """Handle service published event.

        Args:
            node_id: Publisher node ID
            service_id: Service identifier
            service_name: Service name
        """
        self.stats.record_service_published(node_id, service_id, service_name)

    def _on_service_subscribed(self, node_id: int, subscribe_id: int,
                              service_name: str, **kwargs) -> None:
        """Handle service subscribed event.

        Args:
            node_id: Subscriber node ID
            subscribe_id: Subscription identifier
            service_name: Service name
        """
        mode = kwargs.get('mode', 'active')
        self.stats.record_service_subscribed(node_id, subscribe_id, service_name, mode)

    def _on_cluster_formed(self, cluster_id: int, **kwargs) -> None:
        """Handle cluster formation event.

        Args:
            cluster_id: Cluster identifier
        """
        # Find cluster
        for cluster in self.clusters:
            if cluster.cluster_id == cluster_id:
                self.stats.record_cluster_formation(cluster.formation_time)
                self.logger.log_cluster_formation(
                    cluster_id, cluster.formation_time, cluster.get_member_count()
                )
                break

    def create_nodes(self) -> None:
        """Create simulation nodes."""
        node_count = self.config.get('node.count', 20)
        area_size = self.config.get('node.area_size', [100, 100])

        self.logger.info(f"Creating {node_count} nodes in {area_size[0]}x{area_size[1]}m area")

        for i in range(node_count):
            # Random position
            position = (
                random.uniform(0, area_size[0]),
                random.uniform(0, area_size[1])
            )

            # Create node
            node = NANNode(
                self.env,
                node_id=i,
                config=self.config,
                position=position,
                event_bus=self.event_bus,
                channel=self.channel
            )

            self.nodes.append(node)

        self.logger.info(f"Created {len(self.nodes)} nodes")

    def form_clusters(self) -> None:
        """Form NAN clusters based on proximity."""
        # Simple clustering: group nodes that can communicate
        visited = set()
        cluster_id = 0

        for node in self.nodes:
            if node in visited:
                continue

            # Create new cluster
            cluster = Cluster(self.env, cluster_id)
            self.clusters.append(cluster)

            # Find all nodes in range
            to_visit = [node]
            while to_visit:
                current = to_visit.pop()
                if current in visited:
                    continue

                visited.add(current)
                cluster.add_member(current)

                # Find neighbors
                for other in self.nodes:
                    if other not in visited and current.can_communicate_with(other):
                        to_visit.append(other)

            # Elect AM
            cluster.elect_anchor_master()

            # Publish event
            self.event_bus.publish('cluster_formed', cluster_id=cluster_id)

            cluster_id += 1

        self.logger.info(f"Formed {len(self.clusters)} clusters")

    def get_node_by_id(self, node_id: int) -> NANNode:
        """Get node by ID.

        Args:
            node_id: Node identifier

        Returns:
            NANNode if found, None otherwise
        """
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def run(self, duration: int = None) -> None:
        """Run simulation.

        Args:
            duration: Simulation duration in ms (from config if None)
        """
        if duration is None:
            duration = self.config.get('simulation.duration', 60000)

        self.logger.info(f"Starting simulation for {duration} ms")

        # Create nodes
        self.create_nodes()

        # Form clusters
        self.form_clusters()

        # Start all nodes
        for node in self.nodes:
            self.env.process(node.run())

        # Run simulation
        self.env.run(until=duration)

        self.logger.info(f"Simulation completed at {self.env.now} ms")

        # Export results
        self.export_results()

    def export_results(self) -> None:
        """Export simulation results."""
        self.logger.info("Exporting results...")

        # Record hop count distribution
        for node in self.nodes:
            if node.cluster:
                hop_count = node.role_state.hop_count_to_am
                self.stats.record_hop_count(node.node_id, hop_count)

        # Export all results
        self.stats.export_results()

        # Print summary
        self._print_summary()

    def _print_summary(self) -> None:
        """Print simulation summary."""
        discovery_summary = self.stats.get_discovery_summary()
        power_summary = self.stats.get_power_summary()

        self.logger.info("=" * 60)
        self.logger.info("SIMULATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Simulation Duration: {self.env.now} ms")
        self.logger.info(f"Total Nodes: {len(self.nodes)}")
        self.logger.info(f"Total Clusters: {len(self.clusters)}")
        self.logger.info(f"Total Discoveries: {discovery_summary['total_discoveries']}")
        self.logger.info(f"Avg Discovery Latency: {discovery_summary['avg_latency']:.2f} ms")
        self.logger.info(f"Median Discovery Latency: {discovery_summary['median_latency']:.2f} ms")
        self.logger.info(f"Total Energy Consumption: {power_summary['total_energy_mj']:.2f} mJ")
        self.logger.info(f"Average Power per Node: {power_summary['avg_power_mw']:.2f} mW")
        self.logger.info("=" * 60)


def main():
    """Main entry point for simulation."""
    import sys

    config_path = sys.argv[1] if len(sys.argv) > 1 else None

    sim = Simulation(config_path)
    sim.run()


if __name__ == '__main__':
    main()
