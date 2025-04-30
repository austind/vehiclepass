"""Seatbelt status."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle

logger = logging.getLogger(__name__)


class SeatBelts:
    """Seatbelt status."""

    def __init__(self, vehicle: "Vehicle"):
        """Initialize seatbelt status readings from status data and dynamically create properties.

        Args:
            vehicle: Parent vehicle object

        Raises:
            None
        """
        self._vehicle = vehicle
        self._seatbelts = {}
        self._seatbelt_status = self._vehicle._get_metric_value("seatBeltStatus", list)

        for seatbelt in self._seatbelt_status:
            position = seatbelt.get("vehicleOccupantRole", "").lower()
            self._seatbelts[position] = seatbelt["value"]
            setattr(self, position, seatbelt["value"])

    def __repr__(self) -> str:
        """Return string representation showing available seatbelts."""
        positions = list(self._seatbelts.keys())
        return f"SeatBelts(seats={positions})"
