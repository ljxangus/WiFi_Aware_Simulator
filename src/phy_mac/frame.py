"""NAN frame definitions as per 802.11 Annex AQ."""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class FrameType(Enum):
    """NAN frame types."""
    BEACON = "Beacon"
    SDF = "Service Discovery Frame"  # Service Discovery Frame
    DATA = "Data"
    ACK = "ACK"


@dataclass
class NANAddress:
    """NAN MAC address (48-bit)."""
    addr: int

    def __str__(self) -> str:
        """Return formatted MAC address."""
        return ":".join([f"{(self.addr >> (8 * i)) & 0xFF:02X}"
                        for i in range(5, -1, -1)])


@dataclass
class ServiceDescriptor:
    """Service descriptor for SDF frames."""
    service_id: int
    service_name: str
    service_info: bytes
    match_filter: Optional[bytes] = None
    publish_count: int = 0


@dataclass
class NANBeaconFrame:
    """NAN Beacon frame structure."""
    frame_type: FrameType = FrameType.BEACON
    timestamp: int = 0  # TSF timestamp
    beacon_interval: int = 100  # TUs
    cluster_id: int = 0
    am_rank: int = 255
    hop_count: int = 0
    source_addr: int = 0
    supported_channels: List[int] = field(default_factory=lambda: [6])

    def to_bytes(self) -> bytes:
        """Serialize frame to bytes (simplified)."""
        # Simplified serialization
        data = (
            self.timestamp.to_bytes(8, 'little') +
            self.beacon_interval.to_bytes(2, 'little') +
            self.cluster_id.to_bytes(6, 'little') +
            self.am_rank.to_bytes(1, 'little') +
            self.hop_count.to_bytes(1, 'little') +
            self.source_addr.to_bytes(6, 'little')
        )
        return data


@dataclass
class SDFHeader:
    """Service Discovery Frame header."""
    frame_type: FrameType = FrameType.SDF
    source_addr: int = 0
    ndp_available: bool = False
    service_count: int = 0


@dataclass
class NANServiceDiscoveryFrame:
    """NAN Service Discovery Frame."""
    header: SDFHeader
    services: List[ServiceDescriptor]

    def to_bytes(self) -> bytes:
        """Serialize frame to bytes (simplified)."""
        # Simplified serialization
        data = (
            self.header.source_addr.to_bytes(6, 'little') +
            self.header.service_count.to_bytes(1, 'little')
        )
        return data


@dataclass
class NDPScheduleElement:
    """NDP Schedule element for data path indication."""
    ndp_id: int
    channel: int
    start_time: int  # Relative to DW end
    duration: int


@dataclass
class NDPIndicationFrame:
    """NDP Indication frame for service discovery."""
    frame_type: FrameType = FrameType.DATA
    source_addr: int = 0
    destination_addr: int = 0
    ndp_schedule: List[NDPScheduleElement] = field(default_factory=list)
