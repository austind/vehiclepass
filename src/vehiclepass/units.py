"""Unit conversion utilities."""

from dataclasses import dataclass, field
from typing import Literal, TypeVar

from vehiclepass.constants import (
    DECIMAL_PLACES,
    DEFAULT_DISTANCE_UNIT,
    DEFAULT_ELECTRIC_POTENTIAL_UNIT,
    DEFAULT_PRESSURE_UNIT,
    DEFAULT_TEMP_UNIT,
)

T = TypeVar("T")

TemperatureUnit = Literal["c", "f"]
DistanceUnit = Literal["km", "mi"]
PressureUnit = Literal["kpa", "psi"]

unit_label_map = {
    "c": "°C",
    "f": "°F",
    "km": "km",
    "mi": "mi",
    "kpa": "kPa",
    "psi": "psi",
    "v": "V",
    "mv": "mV",
}


@dataclass(frozen=True)
class Temperature:
    """Temperature value with unit conversion capabilities."""

    celsius: float
    _decimal_places: int = field(default=DECIMAL_PLACES)

    @property
    def c(self) -> float:
        """Get temperature in Celsius."""
        return round(self.celsius, self._decimal_places)

    @property
    def f(self) -> float:
        """Get temperature in Fahrenheit."""
        return round((self.celsius * 9 / 5) + 32, self._decimal_places)

    @classmethod
    def from_celsius(cls, value: float, decimal_places: int = DECIMAL_PLACES) -> "Temperature":
        """Create a Temperature instance from a Celsius value."""
        return cls(value, decimal_places)

    @classmethod
    def from_fahrenheit(cls, value: float, decimal_places: int = DECIMAL_PLACES) -> "Temperature":
        """Create a Temperature instance from a Fahrenheit value."""
        return cls((value - 32) * 5 / 9, decimal_places)

    def __str__(self) -> str:
        """Return a string representation of the temperature."""
        return f"{getattr(self, DEFAULT_TEMP_UNIT)}{unit_label_map[DEFAULT_TEMP_UNIT]}"


@dataclass(frozen=True)
class Distance:
    """Distance value with unit conversion capabilities."""

    kilometers: float
    _decimal_places: int = field(default=DECIMAL_PLACES)

    @property
    def km(self) -> float:
        """Get distance in kilometers."""
        return round(self.kilometers, self._decimal_places)

    @property
    def mi(self) -> float:
        """Get distance in miles."""
        return round(self.kilometers * 0.621371, self._decimal_places)

    @classmethod
    def from_kilometers(cls, value: float, decimal_places: int = DECIMAL_PLACES) -> "Distance":
        """Create a Distance instance from a kilometers value."""
        return cls(value, decimal_places)

    @classmethod
    def from_miles(cls, value: float, decimal_places: int = DECIMAL_PLACES) -> "Distance":
        """Create a Distance instance from a miles value."""
        return cls(value / 0.621371, decimal_places)

    def __str__(self) -> str:
        """Return a string representation of the distance."""
        return f"{getattr(self, DEFAULT_DISTANCE_UNIT)} {unit_label_map[DEFAULT_DISTANCE_UNIT]}"


@dataclass(frozen=True)
class Pressure:
    """Pressure value with unit conversion capabilities."""

    kilopascals: float
    _decimal_places: int = field(default=DECIMAL_PLACES)

    @property
    def kpa(self) -> float:
        """Get pressure in kilopascals."""
        return round(self.kilopascals, self._decimal_places)

    @property
    def psi(self) -> float:
        """Get pressure in pounds per square inch."""
        return round(self.kilopascals * 0.145038, self._decimal_places)

    @classmethod
    def from_kilopascals(cls, value: float, decimal_places: int = DECIMAL_PLACES) -> "Pressure":
        """Create a Pressure instance from a kilopascals value."""
        return cls(value, decimal_places)

    @classmethod
    def from_psi(cls, value: float, decimal_places: int = DECIMAL_PLACES) -> "Pressure":
        """Create a Pressure instance from a psi value."""
        return cls(value / 0.145038, decimal_places)

    def __str__(self) -> str:
        """Return a string representation of the pressure."""
        return f"{getattr(self, DEFAULT_PRESSURE_UNIT)} {unit_label_map[DEFAULT_PRESSURE_UNIT]}"


@dataclass(frozen=True)
class ElectricPotential:
    """Electric potential value with unit conversion capabilities."""

    volts: float | int
    _decimal_places: int = field(default=DECIMAL_PLACES)

    @property
    def v(self) -> float:
        """Get electric potential in volts."""
        return round(self.volts, self._decimal_places)

    @property
    def mv(self) -> float:
        """Get electric potential in millivolts."""
        return round(self.volts * 1000, self._decimal_places)

    @classmethod
    def from_volts(cls, value: float, decimal_places: int = DECIMAL_PLACES) -> "ElectricPotential":
        """Create an ElectricPotential instance from a volts value."""
        return cls(value, decimal_places)

    @classmethod
    def from_millivolts(cls, value: float, decimal_places: int = DECIMAL_PLACES) -> "ElectricPotential":
        """Create an ElectricPotential instance from a millivolts value."""
        return cls(value / 1000, decimal_places)

    def __str__(self) -> str:
        """Return a string representation of the electric potential."""
        return f"{getattr(self, DEFAULT_ELECTRIC_POTENTIAL_UNIT)} {unit_label_map[DEFAULT_ELECTRIC_POTENTIAL_UNIT]}"


@dataclass(frozen=True)
class Percentage:
    """Percentage value."""

    percentage: float
    _decimal_places: int = field(default=DECIMAL_PLACES)

    def __str__(self) -> str:
        """Return a string representation of the percentage."""
        return f"{self.percentage * 100}%"
