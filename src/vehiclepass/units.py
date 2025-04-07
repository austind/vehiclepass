"""Unit conversion utilities using Pydantic models."""

import datetime
from typing import Annotated, Literal, Optional, TypeVar

from pydantic import BaseModel, Field, NonNegativeInt
from pydantic.functional_validators import AfterValidator

from vehiclepass.constants import (
    DECIMAL_PLACES,
    DEFAULT_DISTANCE_UNIT,
    DEFAULT_ELECTRIC_POTENTIAL_UNIT,
    DEFAULT_PRESSURE_UNIT,
    DEFAULT_TEMP_UNIT,
    DEFAULT_TIME_UNIT,
)

T = TypeVar("T")

TemperatureUnit = Literal["c", "f"]
DistanceUnit = Literal["km", "mi"]
PressureUnit = Literal["kpa", "psi"]
ElectricPotentialUnit = Literal["v", "mv"]
TimeUnit = Literal["h", "m", "s", "ms", "human_readable"]

# Type aliases for better type checking
Celsius = Annotated[float, AfterValidator(lambda x: round(x, DECIMAL_PLACES))]
Kilometers = Annotated[float, AfterValidator(lambda x: round(x, DECIMAL_PLACES))]
Kilopascals = Annotated[float, AfterValidator(lambda x: round(x, DECIMAL_PLACES))]
Volts = Annotated[float, AfterValidator(lambda x: round(x, DECIMAL_PLACES))]
Seconds = Annotated[float, AfterValidator(lambda x: round(x, DECIMAL_PLACES))]
PercentValue = Annotated[float, AfterValidator(lambda x: round(x, DECIMAL_PLACES))]

# Unit label mapping for string representations
UNIT_LABEL_MAP: dict[str, str] = {
    "c": "°C",
    "f": "°F",
    "km": "km",
    "mi": "mi",
    "kpa": "kPa",
    "psi": "psi",
    "v": "V",
    "mv": "mV",
    "s": "s",
    "m": "m",
    "h": "h",
}


class UnitModel(BaseModel):
    """Base model for unit conversion models."""

    decimal_places: Optional[int] = Field(default=DECIMAL_PLACES, exclude=True)
    _units: tuple[str, ...] = ()
    model_config = {
        "frozen": True,
    }

    def round_value(self, value: float, decimal_places: Optional[NonNegativeInt] = None) -> float:
        """Round a value to the specified decimal places."""
        return round(value, decimal_places or self.decimal_places or DECIMAL_PLACES)

    @property
    def data(self) -> dict[str, float]:
        """Get all data units in a dictionary."""
        return {unit: getattr(self, unit) for unit in self._units}


class Temperature(UnitModel):
    """Temperature value with unit conversion capabilities."""

    celsius: Celsius
    _units = ("c", "f")

    @property
    def c(self) -> float:
        """Get temperature in Celsius."""
        return self.round_value(self.celsius)

    @property
    def f(self) -> float:
        """Get temperature in Fahrenheit."""
        return self.round_value((self.celsius * 9 / 5) + 32)

    @classmethod
    def from_celsius(cls, value: float, decimal_places: Optional[int] = None) -> "Temperature":
        """Create a Temperature instance from a Celsius value."""
        return cls(celsius=value, decimal_places=decimal_places)

    @classmethod
    def from_fahrenheit(cls, value: float, decimal_places: Optional[int] = None) -> "Temperature":
        """Create a Temperature instance from a Fahrenheit value."""
        return cls(celsius=(value - 32) * 5 / 9, decimal_places=decimal_places)

    def __str__(self) -> str:
        """Return a string representation of the temperature."""
        value = getattr(self, DEFAULT_TEMP_UNIT)
        unit = UNIT_LABEL_MAP[DEFAULT_TEMP_UNIT]
        return f"{value}{unit}"


class Distance(UnitModel):
    """Distance value with unit conversion capabilities."""

    kilometers: Kilometers
    _units = ("km", "mi")

    @property
    def km(self) -> float:
        """Get distance in kilometers."""
        return self.round_value(self.kilometers)

    @property
    def mi(self) -> float:
        """Get distance in miles."""
        return self.round_value(self.kilometers * 0.621371)

    @classmethod
    def from_kilometers(cls, value: float, decimal_places: Optional[int] = None) -> "Distance":
        """Create a Distance instance from a kilometers value."""
        return cls(kilometers=value, decimal_places=decimal_places)

    @classmethod
    def from_miles(cls, value: float, decimal_places: Optional[int] = None) -> "Distance":
        """Create a Distance instance from a miles value."""
        return cls(kilometers=value / 0.621371, decimal_places=decimal_places)

    def __str__(self) -> str:
        """Return a string representation of the distance."""
        value = getattr(self, DEFAULT_DISTANCE_UNIT)
        unit = UNIT_LABEL_MAP[DEFAULT_DISTANCE_UNIT]
        return f"{value} {unit}"


class Pressure(UnitModel):
    """Pressure value with unit conversion capabilities."""

    kilopascals: Kilopascals
    _units = ("kpa", "psi", "bar")

    @property
    def bar(self) -> float:
        """Get pressure in bars."""
        return self.round_value(self.kilopascals / 100)

    @property
    def kpa(self) -> float:
        """Get pressure in kilopascals."""
        return self.round_value(self.kilopascals)

    @property
    def psi(self) -> float:
        """Get pressure in pounds per square inch."""
        return self.round_value(self.kilopascals * 0.145038)

    @classmethod
    def from_kilopascals(cls, value: float, decimal_places: Optional[int] = None) -> "Pressure":
        """Create a Pressure instance from a kilopascals value."""
        return cls(kilopascals=value, decimal_places=decimal_places)

    @classmethod
    def from_psi(cls, value: float, decimal_places: Optional[int] = None) -> "Pressure":
        """Create a Pressure instance from a psi value."""
        return cls(kilopascals=value / 0.145038, decimal_places=decimal_places)

    def __str__(self) -> str:
        """Return a string representation of the pressure."""
        value = getattr(self, DEFAULT_PRESSURE_UNIT)
        unit = UNIT_LABEL_MAP[DEFAULT_PRESSURE_UNIT]
        return f"{value} {unit}"


class ElectricPotential(UnitModel):
    """Electric potential value with unit conversion capabilities."""

    volts: Volts
    _units = ("v", "mv")

    @property
    def v(self) -> float:
        """Get electric potential in volts."""
        return self.round_value(self.volts)

    @property
    def mv(self) -> float:
        """Get electric potential in millivolts."""
        return self.round_value(self.volts * 1000)

    @classmethod
    def from_volts(cls, value: float, decimal_places: Optional[int] = None) -> "ElectricPotential":
        """Create an ElectricPotential instance from a volts value."""
        return cls(volts=value, decimal_places=decimal_places)

    @classmethod
    def from_millivolts(cls, value: float, decimal_places: Optional[int] = None) -> "ElectricPotential":
        """Create an ElectricPotential instance from a millivolts value."""
        return cls(volts=value / 1000, decimal_places=decimal_places)

    def __str__(self) -> str:
        """Return a string representation of the electric potential."""
        value = getattr(self, DEFAULT_ELECTRIC_POTENTIAL_UNIT)
        unit = UNIT_LABEL_MAP[DEFAULT_ELECTRIC_POTENTIAL_UNIT]
        return f"{value} {unit}"


class Percentage(UnitModel):
    """Percentage value."""

    value: float = Field(alias="percentage")

    @property
    def percent(self) -> float:
        """Get the rounded percentage value."""
        # Since percents are already decimals, we need to add 2 more decimal places to the value
        return self.round_value(self.value, decimal_places=self.decimal_places + 2 if self.decimal_places else None)

    def __str__(self) -> str:
        """Return a string representation of the percentage."""
        return f"{self.percent * 100}%"


class Duration(UnitModel):
    """Time duration."""

    seconds: Seconds
    _units = ("h", "m", "s", "ms", "human_readable")

    @property
    def h(self) -> float:
        """Get duration in hours."""
        return self.round_value(self.seconds / 3600)

    @property
    def m(self) -> float:
        """Get duration in minutes."""
        return self.round_value(self.seconds / 60)

    @property
    def s(self) -> float:
        """Get duration in seconds."""
        return self.round_value(self.seconds)

    @property
    def ms(self) -> float:
        """Get duration in milliseconds."""
        return self.round_value(self.seconds * 1000)

    @property
    def delta(self) -> datetime.timedelta:
        """Get duration as a datetime.timedelta object."""
        return datetime.timedelta(seconds=self.seconds)

    @property
    def human_readable(self) -> str:
        """Get duration in human readable format."""
        parts = []
        if self.h >= 1:
            parts.append(f"{int(self.h)}h")

        minutes = int(self.m) % 60
        if minutes > 0:
            parts.append(f"{minutes}m")

        remaining_seconds = int(self.seconds) % 60
        if remaining_seconds > 0 or not parts:
            parts.append(f"{remaining_seconds}s")

        return " ".join(parts)

    @classmethod
    def from_seconds(cls, value: float, decimal_places: Optional[int] = None) -> "Duration":
        """Create a Duration instance from a seconds value."""
        return cls(seconds=value, decimal_places=decimal_places)

    def __str__(self) -> str:
        """Return a string representation of the time."""
        if DEFAULT_TIME_UNIT == "human_readable":
            return self.human_readable

        value = getattr(self, DEFAULT_TIME_UNIT)
        unit = UNIT_LABEL_MAP[DEFAULT_TIME_UNIT]
        return f"{value} {unit}"
