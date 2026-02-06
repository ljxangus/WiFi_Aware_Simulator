"""Core modules for Wi-Fi Aware Simulator."""

from .config import Config
from .event_bus import EventBus
# Simulation imports NANNode, which causes circular import if imported here

__all__ = ['Config', 'EventBus']
