"""Tire pressure reading for all vehicle wheels."""

from dataclasses import dataclass, field

from vehiclepass.units import Pressure


@dataclass
class TirePressure:
    """Represents tire pressure readings for all vehicle wheels."""

    _data: dict[str, Pressure] = field(default_factory=dict)
    _decimal_places: int = field(default=2)

    @classmethod
    def from_status_data(cls, tire_pressure_data: list, decimal_places: int = 2) -> "TirePressure":
        """Create a TirePressure instance from status data.

        Args:
            tire_pressure_data: List of tire pressure readings from status JSON
            decimal_places: Number of decimal places for unit conversions (default: 2)

        Returns:
            TirePressure instance with the provided data
        """
        data = {}
        for tire in tire_pressure_data:
            wheel_position = tire["vehicleWheel"].lower()
            data[wheel_position] = Pressure.from_kilopascals(tire["value"], decimal_places=decimal_places)

        instance = cls(_data=data)

        # Create property getter that returns Pressure object
        def make_getter(pos):
            def getter(self):
                """Get tire pressure.

                Returns:
                    Pressure object, or None if position not found
                """
                return self._data.get(pos)

            return getter

        for pos in data:
            setattr(TirePressure, pos, property(make_getter(pos)))

        return instance

    def get_pressure(self, wheel_position: str) -> Pressure | None:
        """Get tire pressure for a specific wheel.

        Args:
            wheel_position: Wheel position identifier (e.g., 'front_left')

        Returns:
            Pressure object, or None if position not found
        """
        return self._data.get(wheel_position.lower())

    def __repr__(self):
        """Return string representation showing available tire positions."""
        positions = list(self._data.keys())
        return f"TirePressure(positions={positions})"
