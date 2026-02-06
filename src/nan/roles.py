"""NAN role definitions and enums."""

from enum import Enum


class NANRole(Enum):
    """NAN Cluster roles defined in 802.11 Annex AQ."""

    ANCHOR_MASTER = "AM"  # Anchor Master - highest priority device
    SYNC_MASTER = "NMS"   # Non-Anchor Master - forwards beacons
    NON_MASTER_SYNC = "NMNS"  # Non-Master Non-Sync - regular device


class RoleState:
    """Role state machine for NAN devices."""

    def __init__(self):
        """Initialize role state."""
        self.current_role = NANRole.NON_MASTER_SYNC
        self.rank = 255  # Device rank (0=highest priority)
        self.hop_count_to_am = 0  # Hops to Anchor Master

    def set_role(self, role: NANRole, hop_count: int = 0) -> None:
        """Set current role.

        Args:
            role: New role
            hop_count: Hop count to AM (for NMS/NMNS)
        """
        self.current_role = role
        self.hop_count_to_am = hop_count

    def can_be_anchor_master(self) -> bool:
        """Check if device can become Anchor Master.

        Returns:
            True if device meets AM requirements
        """
        return self.rank < 255  # Any device with valid rank can be AM

    def is_master(self) -> bool:
        """Check if device is a master (AM or NMS).

        Returns:
            True if device is AM or NMS
        """
        return self.current_role in [NANRole.ANCHOR_MASTER, NANRole.SYNC_MASTER]
