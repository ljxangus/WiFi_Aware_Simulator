"""Tests for TSF clock synchronization."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import simpy
from nan.tsf import TSFClock


@pytest.fixture
def env():
    """Create SimPy environment."""
    return simpy.Environment()


@pytest.fixture
def clock_no_drift(env):
    """Create TSF clock without drift."""
    return TSFClock(env, drift_ppm=0)


@pytest.fixture
def clock_with_drift(env):
    """Create TSF clock with 50ppm drift."""
    return TSFClock(env, drift_ppm=50)


def test_clock_initialization(env, clock_no_drift):
    """Test TSF clock initialization."""
    assert clock_no_drift.tsf == 0
    assert clock_no_drift.drift_ppm == 0
    assert clock_no_drift.get_time() == 0
    assert clock_no_drift.sync_count == 0


def test_get_time_no_drift(env, clock_no_drift):
    """Test time retrieval without drift."""
    # Advance environment
    env.run(100)  # 100 ms

    # TSF should be 100000 us (100 ms)
    assert clock_no_drift.get_time() == 100000


def test_get_time_with_drift(env, clock_with_drift):
    """Test time retrieval with drift."""
    # Advance environment
    env.run(100)  # 100 ms

    # TSF should be affected by drift
    time_with_drift = clock_with_drift.get_time()
    expected_time = 100000 * (1 + 50 / 1e6)

    assert abs(time_with_drift - expected_time) < 1


def test_synchronize(env, clock_no_drift):
    """Test TSF synchronization."""
    # Advance time
    env.run(100)

    # Synchronize to beacon with TSF = 200000
    clock_no_drift.synchronize(200000, rtt_error=0)

    # Check that TSF was updated
    assert clock_no_drift.tsf > 0
    assert clock_no_drift.sync_count == 1


def test_synchronize_with_rtt_error(env, clock_no_drift):
    """Test synchronization with RTT error."""
    # Current time
    current = clock_no_drift.get_time()
    assert current == 0

    # Synchronize with RTT error
    # The sync adjusts: tsf += (beacon_tsf - current + rtt_error)
    clock_no_drift.synchronize(200000, rtt_error=100)

    # Check that RTT error was applied
    # Base TSF was 0, now should be 200100 (200000 + 100)
    current_time = clock_no_drift.get_time()
    assert current_time == 200100


def test_get_drift_error(env, clock_with_drift):
    """Test drift error calculation."""
    # Advance time
    env.run(1000)  # 1000 ms

    # Get drift error
    drift_error = clock_with_drift.get_drift_error()

    # Should be non-zero due to drift
    assert drift_error > 0


def test_reset(env, clock_no_drift):
    """Test TSF reset."""
    # Advance and sync
    env.run(100)
    clock_no_drift.synchronize(200000, rtt_error=0)

    # Reset
    clock_no_drift.reset()

    # Check reset values
    assert clock_no_drift.tsf == 0
    assert clock_no_drift.sync_count == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
