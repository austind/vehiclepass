"""Vehicle status class."""

import datetime
import logging
from typing import TYPE_CHECKING, Any, TypeVar

from vehiclepass.errors import VehiclePassStatusError
from vehiclepass.status.indicators import Indicators
from vehiclepass.status.tire_pressure import TirePressure
from vehiclepass.units import Distance, Temperature

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle

logger = logging.getLogger(__name__)

T = TypeVar("T")


class VehicleStatus:
    """Represents the current status of a vehicle."""

    def __init__(self, vehicle: "Vehicle", decimal_places: int = 2) -> None:
        """Initialize the VehicleStatus object.

        Args:
            vehicle: The Vehicle instance this status belongs to
            decimal_places: Number of decimal places for unit conversions (default: 2)
        """
        self._vehicle = vehicle
        self._status = {}
        self._decimal_places = decimal_places
        self.refresh()
