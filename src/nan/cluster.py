"""NAN Cluster management as per 802.11 Annex AQ."""

import random
from typing import List, Optional
from .roles import NANRole


class Cluster:
    """NAN Cluster managing member devices and role assignment."""

    def __init__(self, env, cluster_id: int):
        """Initialize NAN cluster.

        Args:
            env: SimPy environment
            cluster_id: Unique cluster identifier
        """
        self.env = env
        self.cluster_id = cluster_id
        self.anchor_master = None  # Reference to AM node
        self.members = []  # List of NANNode members
        self.formation_time = None  # Time when cluster formed
        self.cluster_id_beacon = random.randint(0, 2**48 - 1)  # Random Cluster ID

    def add_member(self, node) -> None:
        """Add a node to the cluster.

        Args:
            node: NANNode to add
        """
        if node not in self.members:
            self.members.append(node)
            node.cluster = self

            # Record cluster formation time
            if self.formation_time is None and len(self.members) >= 2:
                self.formation_time = self.env.now

    def remove_member(self, node) -> None:
        """Remove a node from the cluster.

        Args:
            node: NANNode to remove
        """
        if node in self.members:
            self.members.remove(node)
            node.cluster = None

    def elect_anchor_master(self) -> None:
        """Elect Anchor Master based on highest priority.

        Priority criteria (in order):
        1. Lowest rank value
        2. Highest MAC address (if ranks equal)
        """
        if not self.members:
            return

        # Filter devices that can be AM
        candidates = [n for n in self.members if n.role_state.can_be_anchor_master()]

        if not candidates:
            return

        # Select AM based on rank (lower is better)
        # If ranks equal, higher MAC address wins
        self.anchor_master = min(candidates, key=lambda n: (n.role_state.rank, -n.node_id))

        # Update roles
        for member in self.members:
            if member == self.anchor_master:
                member.role_state.set_role(NANRole.ANCHOR_MASTER, hop_count=0)
            else:
                # Calculate hop count to AM
                hop_count = self.calculate_hop_count(member)
                member.role_state.set_role(NANRole.SYNC_MASTER, hop_count=hop_count)

    def calculate_hop_count(self, node) -> int:
        """Calculate hop count from node to Anchor Master.

        Args:
            node: Node to calculate hop count for

        Returns:
            Number of hops to AM
        """
        if node == self.anchor_master:
            return 0

        # Simple distance-based hop count (could be enhanced with routing)
        # In real NAN, hop count is from beacon field
        distance = self._calculate_distance(node, self.anchor_master)
        nominal_range = 50.0  # meters (typical WiFi range)

        return max(1, int(distance / nominal_range))

    def _calculate_distance(self, node1, node2) -> float:
        """Calculate Euclidean distance between two nodes.

        Args:
            node1: First node
            node2: Second node

        Returns:
            Distance in meters
        """
        x1, y1 = node1.position
        x2, y2 = node2.position

        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def get_member_count(self) -> int:
        """Get number of cluster members.

        Returns:
            Number of members
        """
        return len(self.members)

    def is_member(self, node) -> bool:
        """Check if node is a cluster member.

        Args:
            node: Node to check

        Returns:
            True if node is a member
        """
        return node in self.members
