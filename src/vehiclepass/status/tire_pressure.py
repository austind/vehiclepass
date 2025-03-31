"""Tire pressure reading for all vehicle wheels."""

from typing import Literal

from vehiclepass.errors import VehiclePassStatusError
from vehiclepass.units import UnitConverter, UnitPreferences

PressureUnit = Literal["kPa", "psi"]


class TirePressure:
    """Represents tire pressure readings for all vehicle wheels."""

    def __init__(self, tire_pressure_data, unit_preferences: UnitPreferences = None):
        """Initialize tire pressure readings from status data and dynamically create properties.

        Args:
            tire_pressure_data (list): List of tire pressure readings from status JSON
            unit_preferences: Optional unit preferences for pressure conversion

        Raises:
            VehiclePassStatusError: If tire_pressure_data is None or empty
        """
        if not tire_pressure_data:
            raise VehiclePassStatusError("tire_pressure_data cannot be None or empty")

        self._data = {}
        self._unit_converter = UnitConverter(unit_preferences)

        for tire in tire_pressure_data:
            wheel_position = tire["vehicleWheel"].lower()
            # Store original kPa values
            self._data[wheel_position] = tire["value"]

            # Create property getter that handles unit conversion
            def make_getter(pos):
                def getter(self, unit: PressureUnit = None):
                    """Get tire pressure with optional unit conversion.

                    Args:
                        unit: Target unit ('kPa' or 'psi'). If None, uses preference.

                    Returns:
                        Pressure value in specified units
                    """
                    value = self._data.get(pos)
                    if value is None:
                        return None
                    return self._unit_converter.pressure(value, unit)

                return getter

            setattr(TirePressure, wheel_position, property(make_getter(wheel_position)))

    def get_pressure(self, wheel_position: str, unit: PressureUnit = None) -> float | None:
        """Get tire pressure for a specific wheel with optional unit conversion.

        Args:
            wheel_position: Wheel position identifier (e.g., 'front_left')
            unit: Target unit ('kPa' or 'psi'). If None, uses preference.

        Returns:
            Pressure value in specified units, or None if position not found
        """
        value = self._data.get(wheel_position.lower())
        if value is None:
            return None
        return self._unit_converter.pressure(value, unit)

    def __repr__(self):
        """Return string representation showing available tire positions."""
        positions = list(self._data.keys())
        return f"TirePressure(positions={positions})"
