"""Tire pressure reading for all vehicle wheels."""

from vehiclepass.units import Pressure


class TirePressure:
    """Represents tire pressure readings for all vehicle wheels."""

    def __init__(self, tire_pressure_data: list, decimal_places: int = 2) -> None:
        """Initialize tire pressure readings from status data and dynamically create properties.

        Args:
            tire_pressure_data: List of tire pressure readings from status JSON
            decimal_places: Number of decimal places for unit conversions (default: 2)
        """
        self._tires = {}
        for tire in tire_pressure_data:
            tire_position = tire["vehicleWheel"].lower()
            self._tires[tire_position] = Pressure.from_kilopascals(tire["value"], decimal_places=decimal_places)
            setattr(self, tire_position, self._tires[tire_position])

    def __repr__(self):
        """Return string representation showing available tire positions."""
        positions = list(self._tires.keys())
        return f"TirePressure(positions={positions})"
