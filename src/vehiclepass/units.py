"""Unit conversion utilities."""

from dataclasses import dataclass, field
from typing import Literal, TypeVar

T = TypeVar("T")

TemperatureUnit = Literal["c", "f"]
DistanceUnit = Literal["km", "mi"]
PressureUnit = Literal["kpa", "psi"]


@dataclass(frozen=True)
class Temperature:
    """Temperature value with unit conversion capabilities."""

    celsius: float
    _decimal_places: int = field(default=2)

    @property
    def c(self) -> float:
        """Get temperature in Celsius."""
        return round(self.celsius, self._decimal_places)

    @property
    def f(self) -> float:
        """Get temperature in Fahrenheit."""
        return round((self.celsius * 9 / 5) + 32, self._decimal_places)

    @classmethod
    def from_celsius(cls, value: float, decimal_places: int = 2) -> "Temperature":
        """Create a Temperature instance from a Celsius value."""
        return cls(value, decimal_places)

    @classmethod
    def from_fahrenheit(cls, value: float, decimal_places: int = 2) -> "Temperature":
        """Create a Temperature instance from a Fahrenheit value."""
        return cls((value - 32) * 5 / 9, decimal_places)


@dataclass(frozen=True)
class Distance:
    """Distance value with unit conversion capabilities."""

    kilometers: float
    _decimal_places: int = field(default=2)

    @property
    def km(self) -> float:
        """Get distance in kilometers."""
        return round(self.kilometers, self._decimal_places)

    @property
    def mi(self) -> float:
        """Get distance in miles."""
        return round(self.kilometers * 0.621371, self._decimal_places)

    @classmethod
    def from_kilometers(cls, value: float, decimal_places: int = 2) -> "Distance":
        """Create a Distance instance from a kilometers value."""
        return cls(value, decimal_places)

    @classmethod
    def from_miles(cls, value: float, decimal_places: int = 2) -> "Distance":
        """Create a Distance instance from a miles value."""
        return cls(value / 0.621371, decimal_places)


@dataclass(frozen=True)
class Pressure:
    """Pressure value with unit conversion capabilities."""

    kilopascals: float
    _decimal_places: int = field(default=2)

    @property
    def kpa(self) -> float:
        """Get pressure in kilopascals."""
        return round(self.kilopascals, self._decimal_places)

    @property
    def psi(self) -> float:
        """Get pressure in pounds per square inch."""
        return round(self.kilopascals * 0.145038, self._decimal_places)

    @classmethod
    def from_kilopascals(cls, value: float, decimal_places: int = 2) -> "Pressure":
        """Create a Pressure instance from a kilopascals value."""
        return cls(value, decimal_places)

    @classmethod
    def from_psi(cls, value: float, decimal_places: int = 2) -> "Pressure":
        """Create a Pressure instance from a psi value."""
        return cls(value / 0.145038, decimal_places)
