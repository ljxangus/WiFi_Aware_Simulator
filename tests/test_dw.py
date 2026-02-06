"""Tests for Discovery Window scheduling."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import simpy
from discovery.discovery_window import DiscoveryWindow
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


@pytest.fixture
def discovery_window(env, sample_node, config, channel):
    """Create Discovery Window instance."""
    return DiscoveryWindow(env, sample_node, config, channel)


def test_dw_initialization(discovery_window):
    """Test Discovery Window initialization."""
    assert discovery_window.dw_interval == 512
    assert discovery_window.dw_duration == 16
    assert discovery_window.dw_active is False
    assert discovery_window.dw_count == 0


def test_time_to_next_dw(env, discovery_window):
    """Test time calculation to next DW."""
    # At start, should be full interval
    assert discovery_window.time_to_next_dw() == 512

    # Advance time
    env.run(100)

    # Should be less than full interval
    assert discovery_window.time_to_next_dw() == 412


def test_is_dw_active(discovery_window):
    """Test DW active state."""
    assert discovery_window.is_dw_active() is False


def test_dw_cycle(env, discovery_window):
    """Test DW cycle timing."""
    # Start DW process
    env.process(discovery_window.run())

    # Create new environment for this test to ensure clean state
    test_env = simpy.Environment()
    test_dw = DiscoveryWindow(
        test_env,
        discovery_window.node,
        discovery_window.config,
        discovery_window.channel
    )
    test_env.process(test_dw.run())

    # Run until first DW
    test_env.run(513)

    # Check that DW was triggered
    assert test_dw.dw_count == 1
    assert test_dw.last_dw_time == 512


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
