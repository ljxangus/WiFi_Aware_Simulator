"""Simulation logger for Wi-Fi Aware Simulator."""

import logging
from pathlib import Path
from datetime import datetime


class SimulationLogger:
    """Logger for simulation events."""

    def __init__(self, name: str = "NAN_Simulator", log_dir: str = "output",
                 log_level: int = logging.INFO):
        """Initialize simulation logger.

        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Logging level
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"simulation_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def info(self, message: str) -> None:
        """Log info message.

        Args:
            message: Message to log
        """
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message.

        Args:
            message: Message to log
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message.

        Args:
            message: Message to log
        """
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """Log debug message.

        Args:
            message: Message to log
        """
        self.logger.debug(message)

    def log_discovery(self, subscriber_id: int, publisher_id: int,
                     service_name: str, latency: float) -> None:
        """Log service discovery event.

        Args:
            subscriber_id: Subscriber node ID
            publisher_id: Publisher node ID
            service_name: Name of discovered service
            latency: Discovery latency in ms
        """
        self.info(
            f"Discovery: Node {subscriber_id} discovered service '{service_name}' "
            f"from Node {publisher_id} (latency: {latency:.2f} ms)"
        )

    def log_cluster_formation(self, cluster_id: int, time_ms: float,
                            member_count: int) -> None:
        """Log cluster formation.

        Args:
            cluster_id: Cluster identifier
            time_ms: Formation time in ms
            member_count: Number of members
        """
        self.info(
            f"Cluster {cluster_id} formed at {time_ms:.2f} ms "
            f"with {member_count} members"
        )

    def log_power_stats(self, node_id: int, energy_mj: float,
                       avg_power_mw: float) -> None:
        """Log power statistics.

        Args:
            node_id: Node identifier
            energy_mj: Total energy consumption in mJ
            avg_power_mw: Average power in mW
        """
        self.info(
            f"Node {node_id}: Energy={energy_mj:.2f} mJ, "
            f"Avg Power={avg_power_mw:.2f} mW"
        )
