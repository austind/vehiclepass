"""Unit conversion utilities."""

import os
from dataclasses import dataclass
from typing import Literal, TypeVar

from pint import UnitRegistry

T = TypeVar("T")

TemperatureUnit = Literal["C", "F"]
DistanceUnit = Literal["km", "mi"]
PressureUnit = Literal["kPa", "psi"]


@dataclass
class UnitPreferences:
    """User preferences for unit display."""

    temperature: TemperatureUnit = "F"
    distance: DistanceUnit = "mi"
    pressure: PressureUnit = "psi"
    decimal_places: int = 2  # Added decimal places preference


class UnitConverter:
    """Handles unit conversions with support for default preferences."""

    def __init__(self, preferences: UnitPreferences = None):
        """Initialize the unit converter.

        Args:
            preferences: Optional unit preferences. If None, reads from environment.
                       Includes decimal_places for rounding precision (default: 2)
        """
        self.ureg = UnitRegistry()
        if preferences is None:
            preferences = UnitPreferences(
                temperature=os.getenv("TEMP_UNIT", "F"),
                distance=os.getenv("DISTANCE_UNIT", "mi"),
                pressure=os.getenv("PRESSURE_UNIT", "psi"),
                decimal_places=int(os.getenv("DECIMAL_PLACES", "2")),
            )
        self.preferences = preferences

    def temperature(self, value: float, unit: TemperatureUnit = None) -> float:
        """Convert temperature between Celsius and Fahrenheit.

        Args:
            value: Temperature value in Celsius
            unit: Target unit ('C' or 'F'). If None, uses preference.

        Returns:
            Converted temperature value rounded to configured decimal places
        """
        unit = unit or self.preferences.temperature
        return round((value * self.ureg.degC).to(unit).magnitude, self.preferences.decimal_places)

    def distance(self, value: float, unit: DistanceUnit = None) -> float:
        """Convert distance between kilometers and miles.

        Args:
            value: Distance value in kilometers
            unit: Target unit ('km' or 'mi'). If None, uses preference.

        Returns:
            Converted distance value rounded to configured decimal places
        """
        unit = unit or self.preferences.distance
        return round((value * self.ureg.kilometer).to(unit).magnitude, self.preferences.decimal_places)

    def pressure(self, value: float, unit: PressureUnit = None) -> float:
        """Convert pressure between kPa and psi.

        Args:
            value: Pressure value in kPa
            unit: Target unit ('kPa' or 'psi'). If None, uses preference.

        Returns:
            Converted pressure value rounded to configured decimal places
        """
        unit = unit or self.preferences.pressure
        return round((value * self.ureg.kilopascal).to(unit).magnitude, self.preferences.decimal_places)

    def __call__(self, value: float, from_unit: str, to_unit: str = None) -> float:
        """Convert any supported unit to another.

        Args:
            value: Value to convert
            from_unit: Source unit (e.g., 'degC', 'kilometer', 'kilopascal')
            to_unit: Target unit (e.g., 'degF', 'mile', 'pound_force_per_square_inch')
                    If None, uses default preferences based on unit type.

        Returns:
            Converted value rounded to configured decimal places
        """
        if to_unit is None:
            # Map unit types to preferences
            if from_unit in ("degC", "degF"):
                to_unit = self.preferences.temperature
            elif from_unit in ("kilometer", "mile"):
                to_unit = self.preferences.distance
            elif from_unit in ("kilopascal", "pound_force_per_square_inch"):
                to_unit = self.preferences.pressure
            else:
                raise ValueError(f"Unknown unit type: {from_unit}")

        return round((value * getattr(self.ureg, from_unit)).to(to_unit).magnitude, self.preferences.decimal_places)
