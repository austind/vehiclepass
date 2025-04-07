"""Tire pressure reading for all vehicle tires."""

import logging
from typing import TYPE_CHECKING

from vehiclepass._types import TirePressureStatus
from vehiclepass.errors import StatusError
from vehiclepass.units import Pressure

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle

logger = logging.getLogger(__name__)


class Tire:
    """Represents tire status for a single tire."""

    def __init__(self, vehicle: "Vehicle", tire_position: str, pressure: Pressure, status: TirePressureStatus) -> None:
        """Initialize tire status for a single tire."""
        self._vehicle = vehicle
        self._tire_position = tire_position
        self.pressure = pressure
        self.status = status

    def __repr__(self):
        """Return string representation showing tire position and pressure."""
        return f"Tire(position={self._tire_position}, pressure={self.pressure})"


class Tires:
    """Represents tire status for all vehicle tires."""

    def __init__(self, vehicle: "Vehicle") -> None:
        """Initialize tire status from status data and dynamically create properties.

        Args:
            vehicle: The parent Vehicle object
        """
        self._vehicle = vehicle
        self._tires = {}
        for tire in self._vehicle._get_metric_value("tirePressure", list):
            tire_position = tire["vehicleWheel"].lower()
            logger.debug("Tire position: %s", tire_position)
            self._tires[tire_position] = {"pressure": tire["value"]}

        for tire in self._vehicle._get_metric_value("tirePressureStatus", list):
            tire_position = tire["vehicleWheel"].lower()
            self._tires[tire_position].update({"status": tire["value"]})

        for tire_position, data in self._tires.items():
            setattr(
                self,
                tire_position,
                Tire(
                    self._vehicle,
                    tire_position,
                    pressure=Pressure.from_kilopascals(data["pressure"]),
                    status=data["status"],
                ),
            )

    @property
    def system_status(self) -> str:
        """Get the system status of the tire pressure monitoringsystem."""
        try:
            return self._vehicle._get_metric_value("tirePressureSystemStatus", list)[0]["value"]
        except (IndexError, KeyError) as exc:
            raise StatusError("Tire pressure monitoring system status not found") from exc

    def __repr__(self):
        """Return string representation showing available tire positions."""
        positions, values = zip(*self._tires.items())
        return f"Tires(positions={positions}, values={values})"
