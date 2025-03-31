"""Vehicle status class."""

import datetime
import logging
from typing import TYPE_CHECKING, Any, TypeVar

from pint import UnitRegistry

from vehiclepass.errors import VehiclePassStatusError
from vehiclepass.status.doors import DoorStatus
from vehiclepass.status.indicators import Indicators
from vehiclepass.status.tire_pressure import TirePressure
from vehiclepass.units import UnitConverter, UnitPreferences

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle

logger = logging.getLogger(__name__)

ureg = UnitRegistry()

T = TypeVar("T")


def get_metric_value(data: dict, metric_name: str, expected_type: type[T] = Any) -> T:
    """Get a value from the metrics dictionary with error handling.

    Args:
        data: The data dictionary containing metrics
        metric_name: The name of the metric to retrieve
        expected_type: The expected type of the value (optional)

    Returns:
        The metric value, rounded to 2 decimal places if numeric

    Raises:
        VehiclePassStatusError: If the metric is not found or invalid
    """
    try:
        metric = data.get("metrics", {}).get(metric_name, {})
        if not metric or "value" not in metric:
            raise VehiclePassStatusError(f"{metric_name} not found in metrics")

        value = metric["value"]
        if expected_type is not Any and not isinstance(value, expected_type):
            raise VehiclePassStatusError(f"Invalid {metric_name} type")

        # Round numeric values to 2 decimal places
        if isinstance(value, float):
            value = round(value, 2)

        return value
    except Exception as e:
        if isinstance(e, VehiclePassStatusError):
            raise
        raise VehiclePassStatusError(f"Error getting {metric_name}: {e!s}") from e


class VehicleStatus:
    """Represents the current status of a vehicle."""

    def __init__(self, vehicle: "Vehicle", unit_preferences: UnitPreferences = None) -> None:
        """Initialize the VehicleStatus object.

        Args:
            vehicle: The Vehicle instance this status belongs to
            unit_preferences: Optional unit preferences for conversions
        """
        self._vehicle = vehicle
        self._status_data = {}
        self._unit_converter = UnitConverter(unit_preferences)
        self.refresh()

    def _get_door_metric(self, metric_name: str) -> str:
        """Get a door-related metric that uses the ALL_DOORS filter.

        Args:
            metric_name: The name of the door metric to retrieve

        Returns:
            The door metric value

        Raises:
            VehiclePassStatusError: If the metric is not found or invalid
        """
        try:
            if "metrics" not in self._status_data or metric_name not in self._status_data["metrics"]:
                raise VehiclePassStatusError(f"{metric_name} not found in metrics")

            status = next(
                (x for x in self._status_data["metrics"][metric_name] if x.get("vehicleDoor") == "ALL_DOORS"),
                None,
            )
            if not status or "value" not in status:
                raise VehiclePassStatusError(f"All doors {metric_name} not found")

            return status["value"]
        except Exception as e:
            if isinstance(e, VehiclePassStatusError):
                raise
            raise VehiclePassStatusError(f"Error getting {metric_name}: {e!s}") from e

    def _get_metric_value(self, metric_name: str, expected_type: type[T] = Any) -> T:
        """Get a value from the metrics dictionary with error handling.

        Args:
            metric_name: The name of the metric to retrieve
            expected_type: The expected type of the value (optional)

        Returns:
            The metric value, rounded to 2 decimal places if numeric

        Raises:
            VehiclePassStatusError: If the metric is not found or invalid
        """
        try:
            metric = self._status_data.get("metrics", {}).get(metric_name, {})
            if not metric or "value" not in metric:
                raise VehiclePassStatusError(f"{metric_name} not found in metrics")

            value = metric["value"]
            if expected_type is not Any and not isinstance(value, expected_type):
                raise VehiclePassStatusError(f"Invalid {metric_name} type")

            return value
        except Exception as e:
            if isinstance(e, VehiclePassStatusError):
                raise
            raise VehiclePassStatusError(f"Error getting {metric_name}: {e!s}") from e

    @property
    def alarm(self) -> str:
        """Get the alarm status."""
        return self._get_metric_value("alarmStatus", str)

    @property
    def battery_charge(self) -> float:
        """Get the battery state of charge."""
        return self._get_metric_value("batteryStateOfCharge", float)

    @property
    def battery_level(self) -> float | None:
        """Get the battery state of charge percentage."""
        return self._get_metric_value("batteryStateOfCharge", float)

    @property
    def battery_voltage(self) -> float:
        """Get the battery voltage."""
        return self._get_metric_value("batteryVoltage", float)

    @property
    def compass_direction(self) -> str:
        """Get the compass direction."""
        return self._get_metric_value("compassDirection", str)

    @property
    def door_locks(self) -> str:
        """Get the door lock status."""
        return self._get_door_metric("doorLockStatus")

    @property
    def doors(self) -> DoorStatus:
        """Get the door status for all doors.

        Returns:
            DoorStatus object containing status for all doors

        Raises:
            VehiclePassStatusError: If door status is not found in metrics
        """
        try:
            if "metrics" not in self._status_data or "doorStatus" not in self._status_data["metrics"]:
                raise VehiclePassStatusError("Door status not found in metrics")
            status = self._status_data["metrics"]["doorStatus"]
            if not isinstance(status, list):
                raise VehiclePassStatusError("Invalid door status format")
            return DoorStatus(status)
        except Exception as e:
            if isinstance(e, VehiclePassStatusError):
                raise
            raise VehiclePassStatusError(f"Error getting door status: {e!s}") from e

    @property
    def fuel_level(self) -> float | None:
        """Get the fuel level."""
        return self._get_metric_value("fuelLevel", float)

    @property
    def fuel_range(self) -> float | None:
        """Get the fuel range using the configured unit preferences.

        Returns:
            The fuel range in the preferred units, or None if not available.
        """
        value = self._get_metric_value("fuelRange", float)
        if value is None:
            return None
        return self._unit_converter.distance(value)

    @property
    def gear_lever_position(self) -> str:
        """Get the gear lever position."""
        return self._get_metric_value("gearLeverPosition", str)

    @property
    def hood(self) -> str:
        """Get the hood status."""
        return self._get_metric_value("hoodStatus", str)

    @property
    def indicators(self) -> Indicators:
        """Get the vehicle indicators status."""
        return Indicators(self._status_data)

    @property
    def is_locked(self) -> bool:
        """Check if the vehicle is locked."""
        try:
            if not isinstance(self._status_data, dict) or "metrics" not in self._status_data:
                raise VehiclePassStatusError("Invalid status response format")

            door_lock_status = self._status_data["metrics"].get("doorLockStatus")
            if not door_lock_status:
                raise VehiclePassStatusError("No door lock status found in metrics")

            all_doors_status = next(
                (x for x in door_lock_status if x.get("vehicleDoor") == "ALL_DOORS"),
                None,
            )
            if not all_doors_status or "value" not in all_doors_status:
                raise VehiclePassStatusError("Door lock status not found in status response")

            return all_doors_status["value"] == "LOCKED"

        except Exception as e:
            if isinstance(e, VehiclePassStatusError):
                raise
            raise VehiclePassStatusError(f"Error checking lock status: {e!s}") from e

    @property
    def is_not_running(self) -> bool:
        """Check if the vehicle is not running."""
        return not self.is_running

    @property
    def is_running(self) -> bool:
        """Check if the vehicle is running."""
        ignition_status = self._status_data["metrics"].get("ignitionStatus")
        if not ignition_status or "value" not in ignition_status:
            raise VehiclePassStatusError("No ignition status found in metrics")

        return ignition_status.get("value", "").lower() == "on"

    @property
    def is_unlocked(self) -> bool:
        """Check if the vehicle is unlocked."""
        return not self.is_locked

    @property
    def odometer(self) -> float | None:
        """Get the odometer reading using the configured unit preferences.

        Returns:
            The odometer reading in the preferred units, or None if not available.
        """
        value = self._get_metric_value("odometer", float)
        if value is None:
            return None
        return self._unit_converter.distance(value)

    @property
    def outside_temp(self) -> float | None:
        """Get the outside temperature using the configured unit preferences.

        Returns:
            The temperature in the preferred units, or None if not available.
        """
        value = self._get_metric_value("outsideTemperature", float)
        if value is None:
            return None
        return self._unit_converter.temperature(value)

    @property
    def raw(self) -> dict:
        """Get the raw status data."""
        return self._status_data

    def refresh(self) -> None:
        """Refresh the vehicle status data."""
        self._status_data = self._vehicle._request("GET", f"{self._vehicle.telemetry_url}/{self._vehicle.vin}")

    @property
    def shutoff_time(self) -> datetime.datetime:
        """Get the UTC time when the vehicle will shut off.

        Raises:
            VehiclePassStatusError: If the countdown timer is not available or invalid.
        """
        seconds = self.shutoff_time_seconds
        return datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=seconds)

    @property
    def shutoff_time_seconds(self) -> float:
        """Get the number of seconds remaining until vehicle shutoff.

        Raises:
            VehiclePassStatusError: If the countdown timer is not available or invalid.
        """
        try:
            countdown_seconds = self._get_metric_value("remoteStartCountdownTimer", float)
            if countdown_seconds < 0:
                raise VehiclePassStatusError(f"Invalid countdown timer value: negative duration ({countdown_seconds})")
            return countdown_seconds
        except Exception as e:
            if isinstance(e, VehiclePassStatusError):
                raise
            raise VehiclePassStatusError(f"Error getting shutoff time seconds: {e!s}") from e

    @property
    def tire_pressure(self) -> TirePressure:
        """Get tire pressure readings."""
        return TirePressure(self._status_data.get("metrics", {}).get("tirePressure", []))
