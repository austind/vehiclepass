"""Vehicle status class."""

import datetime
import logging
from typing import TYPE_CHECKING, Any, TypeVar

from vehiclepass.errors import VehiclePassStatusError
from vehiclepass.status.doors import Doors
from vehiclepass.status.indicators import Indicators
from vehiclepass.status.tire_pressure import TirePressure
from vehiclepass.units import Distance, Temperature

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle

logger = logging.getLogger(__name__)

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

    def __init__(self, vehicle: "Vehicle", decimal_places: int = 2) -> None:
        """Initialize the VehicleStatus object.

        Args:
            vehicle: The Vehicle instance this status belongs to
            decimal_places: Number of decimal places for unit conversions (default: 2)
        """
        self._vehicle = vehicle
        self._status_data = {}
        self._decimal_places = decimal_places
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
    def battery_level(self) -> float:
        """Get the battery state of charge percentage."""
        return self._get_metric_value("batteryStateOfCharge", float) / 100

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
    def doors(self) -> Doors:
        """Get the door status for all doors.

        Returns:
            Doors object containing status for all doors
        """
        return Doors(self._vehicle)

    @property
    def fuel_level(self) -> float:
        """Get the fuel level."""
        return self._get_metric_value("fuelLevel", float) / 100

    @property
    def fuel_range(self) -> Distance:
        """Get the fuel range using the configured unit preferences.

        Returns:
            The fuel range as a Distance object.
        """
        value = self._get_metric_value("fuelRange", float)
        if value is None:
            return None
        return Distance.from_kilometers(value, decimal_places=self._decimal_places)

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
        return Indicators(self._status_data.get("metrics", {}).get("indicators", []))

    @property
    def is_not_running(self) -> bool:
        """Check if the vehicle is not running."""
        return self.engine == "STOPPED"

    @property
    def is_running(self) -> bool:
        """Check if the vehicle is running."""
        return self.engine == "RUNNING"

    @property
    def odometer(self) -> Distance:
        """Get the odometer reading using the configured unit preferences.

        Returns:
            The odometer reading as a Distance object.
        """
        value = self._get_metric_value("odometer", float)
        if value is None:
            return None
        return Distance.from_miles(value, decimal_places=self._decimal_places)

    @property
    def outside_temp(self) -> Temperature:
        """Get the outside temperature using the configured unit preferences.

        Returns:
            The outside temperature as a Temperature object.
        """
        value = self._get_metric_value("outsideTemperature", float)
        if value is None:
            return None
        return Temperature.from_celsius(value, decimal_places=self._decimal_places)

    @property
    def raw(self) -> dict:
        """Get the raw status data."""
        return self._status_data

    def refresh(self) -> None:
        """Refresh the vehicle status data."""
        self._status_data = self._vehicle._request("GET", f"{self._vehicle.telemetry_url}/{self._vehicle.vin}")

    @property
    def shutoff_time(self) -> datetime.datetime:
        """Get the vehicle shutoff time."""
        return datetime.datetime.fromtimestamp(self.shutoff_time_seconds)

    @property
    def shutoff_time_seconds(self) -> float:
        """Get the vehicle shutoff time in seconds since epoch."""
        return self._get_metric_value("shutoffTime", float)

    @property
    def tire_pressure(self) -> TirePressure:
        """Get the tire pressure readings.

        Raises:
            VehiclePassStatusError: If tire pressure data is not available
        """
        tire_pressure_data = self._status_data.get("metrics", {}).get("tirePressure", [])
        if not tire_pressure_data:
            raise VehiclePassStatusError("Tire pressure data not found")

        return TirePressure.from_status_data(tire_pressure_data, decimal_places=self._decimal_places)
