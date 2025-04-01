"""Tire pressure reading for all vehicle wheels."""

from typing import TYPE_CHECKING

from vehiclepass.units import Pressure

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle


class TirePressure:
    """Represents tire pressure readings for all vehicle wheels."""

    def __init__(self, vehicle: "Vehicle") -> None:
        """Initialize tire pressure readings from status data and dynamically create properties.

        Args:
            vehicle: The parent Vehicle object
        """
        self._vehicle = vehicle
        self._tires = {}
        for tire in self._vehicle._get_metric_value("tirePressure", list):
            tire_position = tire["vehicleWheel"].lower()
            self._tires[tire_position] = Pressure.from_kilopascals(tire["value"])
            setattr(self, tire_position, self._tires[tire_position])

    def __repr__(self):
        """Return string representation showing available tire positions."""
        positions = list(self._tires.keys())
        return f"TirePressure(positions={positions})"
