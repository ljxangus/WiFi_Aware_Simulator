"""Tests for NAN Cluster management."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import simpy
from nan.cluster import Cluster
from nan.roles import NANRole
from node.nan_node import NANNode
from core.config import Config
from core.event_bus import EventBus
from phy_mac.channel import ChannelModel


@pytest.fixture
def env():
    """Create SimPy environment."""
    return simpy.Environment()


@pytest.fixture
def config():
    """Create test configuration."""
    return Config()


@pytest.fixture
def channel(env, config):
    """Create channel model."""
    return ChannelModel(env, config)


@pytest.fixture
def event_bus():
    """Create event bus."""
    return EventBus()


@pytest.fixture
def sample_node(env, config, event_bus, channel):
    """Create a sample NAN node."""
    return NANNode(
        env,
        node_id=0,
        config=config,
        position=(50.0, 50.0),
        event_bus=event_bus,
        channel=channel
    )


def test_cluster_creation(env):
    """Test cluster initialization."""
    cluster = Cluster(env, cluster_id=0)

    assert cluster.cluster_id == 0
    assert cluster.anchor_master is None
    assert len(cluster.members) == 0
    assert cluster.formation_time is None


def test_add_member(env, sample_node):
    """Test adding member to cluster."""
    cluster = Cluster(env, cluster_id=0)

    cluster.add_member(sample_node)

    assert len(cluster.members) == 1
    assert sample_node in cluster.members
    assert sample_node.cluster == cluster


def test_remove_member(env, sample_node):
    """Test removing member from cluster."""
    cluster = Cluster(env, cluster_id=0)

    cluster.add_member(sample_node)
    cluster.remove_member(sample_node)

    assert len(cluster.members) == 0
    assert sample_node not in cluster.members
    assert sample_node.cluster is None


def test_elect_anchor_master(env, config, event_bus, channel):
    """Test Anchor Master election."""
    cluster = Cluster(env, cluster_id=0)

    # Create multiple nodes with different ranks
    nodes = []
    for i in range(5):
        node = NANNode(
            env,
            node_id=i,
            config=config,
            position=(50.0 + i * 10, 50.0),
            event_bus=event_bus,
            channel=channel
        )
        node.role_state.rank = i * 10  # Different ranks
        nodes.append(node)
        cluster.add_member(node)

    # Elect AM
    cluster.elect_anchor_master()

    # Check that AM is elected
    assert cluster.anchor_master is not None
    assert cluster.anchor_master.role_state.current_role == NANRole.ANCHOR_MASTER

    # Check that AM has lowest rank
    assert cluster.anchor_master.role_state.rank == min(
        n.role_state.rank for n in nodes
    )


def test_calculate_hop_count(env, config, event_bus, channel):
    """Test hop count calculation."""
    cluster = Cluster(env, cluster_id=0)

    # Create AM
    am = NANNode(
        env,
        node_id=0,
        config=config,
        position=(50.0, 50.0),
        event_bus=event_bus,
        channel=channel
    )
    am.role_state.rank = 0
    cluster.add_member(am)

    # Create distant node
    distant_node = NANNode(
        env,
        node_id=1,
        config=config,
        position=(150.0, 150.0),
        event_bus=event_bus,
        channel=channel
    )
    cluster.add_member(distant_node)

    cluster.elect_anchor_master()

    # Check hop count
    assert am.role_state.hop_count_to_am == 0
    assert distant_node.role_state.hop_count_to_am >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
