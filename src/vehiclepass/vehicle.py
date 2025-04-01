"""Vehicle class."""

import datetime
import json
import logging
import os
import time
from collections.abc import Callable
from typing import Any, Literal, TypeVar

import httpx
from dotenv import load_dotenv

from vehiclepass.constants import (
    AUTONOMIC_AUTH_URL,
    AUTONOMIC_COMMAND_BASE_URL,
    AUTONOMIC_TELEMETRY_BASE_URL,
    FORDPASS_APPLICATION_ID,
    FORDPASS_AUTH_URL,
    FORDPASS_USER_AGENT,
    LOGIN_USER_AGENT,
)
from vehiclepass.doors import Doors
from vehiclepass.errors import VehiclePassCommandError, VehiclePassStatusError
from vehiclepass.indicators import Indicators
from vehiclepass.tire_pressure import TirePressure
from vehiclepass.units import Distance, Temperature

load_dotenv()

logger = logging.getLogger(__name__)


VehicleCommand = Literal["remoteStart", "cancelRemoteStart", "lock", "unlock"]

T = TypeVar("T")


class Vehicle:
    """A client for the VehiclePass API."""

    def __init__(
        self,
        username: str = os.getenv("FORDPASS_USERNAME", ""),
        password: str = os.getenv("FORDPASS_PASSWORD", ""),
        vin: str = os.getenv("FORDPASS_VIN", ""),
    ):
        """Initialize the VehiclePass client."""
        if not username or not password or not vin:
            raise ValueError("FordPass username (email address), password, and VIN are required")
        self.username = username
        self.password = password
        self.vin = vin
        self.fordpass_token = None
        self.autonomic_token = None
        self.http_client = httpx.Client()
        self.http_client.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": "en-US",
                "Accept-Encoding": "gzip, deflate, br",
            }
        )
        self._status = {}

    def __enter__(self) -> "Vehicle":
        """Enter the context manager."""
        self.auth()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        self.http_client.close()

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """Make an HTTP request and return the JSON response.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: The URL to request
            **kwargs: Additional arguments to pass to the httpx.request() method

        Returns:
            dict: JSON response from the API
        """
        response = self.http_client.request(method, url, **kwargs)
        logger.debug(f"Request to {url} returned status: {response.status_code}")
        try:
            logger.debug(f"Response: \n{json.dumps(response.json(), indent=2)}")
        except json.JSONDecodeError:
            logger.debug(f"Response: \n{response.text}")
        if response.status_code >= 400:
            try:
                logger.error("Response: \n%s", json.dumps(response.json(), indent=2))
            except json.JSONDecodeError:
                logger.error("Response: \n%s", response.text)
        response.raise_for_status()
        return response.json()

    def _get_fordpass_token(self) -> None:
        """Get a FordPass token."""
        self.http_client.headers["User-Agent"] = LOGIN_USER_AGENT

        json = {
            "username": self.username,
            "password": self.password,
        }
        result = self._request("POST", FORDPASS_AUTH_URL, json=json)
        self.fordpass_token = result["access_token"]
        logger.info("Obtained FordPass token")

    def _get_autonomic_token(self) -> None:
        """Get an Autonomic token."""
        data = {
            "subject_token": self.fordpass_token,
            "subject_issuer": "fordpass",
            "client_id": "fordpass-prod",
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        }
        result = self._request("POST", AUTONOMIC_AUTH_URL, data=data)
        self.autonomic_token = result["access_token"]
        logger.info("Obtained Autonomic token")

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
            metric = self.status.get("metrics", {}).get(metric_name, {})
            if not metric:
                raise VehiclePassStatusError(f"{metric_name} not found in metrics")

            # If metric has a value key, use it, otherwise use the metric itself
            # e.g. tirePressure is a list of dictionaries, each with a value key
            if "value" in metric:
                value = metric["value"]
            else:
                value = metric

            if expected_type is not Any and not isinstance(value, expected_type):
                raise VehiclePassStatusError(f"Invalid {metric_name} type")
            return value
        except Exception as e:
            if isinstance(e, VehiclePassStatusError):
                raise
            raise VehiclePassStatusError(f"Error getting {metric_name}: {e!s}") from e

    def _send_command(
        self,
        command: VehicleCommand,
        verify: bool = False,
        verify_delay: float | int = 30.0,
        verify_predicate: Callable | None = None,
        success_msg: str = 'Command "%s" completed successfully',
        fail_msg: str = 'Command "%s" failed to complete',
    ) -> dict:
        """Send a command to the vehicle.

        Args:
            command: The command to send
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success
            verify_predicate: A predicate to verify the command's success
            success_msg: The message to log if the command succeeds. If "%s" is present, it will be
                replaced with the value passed in `command`.
            fail_msg: The message to log if the command fails. If "%s" is present, it will be replaced
                with the value passed in `command`.

        Returns:
            dict: The response from the command
        """
        if verify and not verify_predicate:
            raise ValueError("verify_predicate is required if verify is True")
        if not callable(verify_predicate):
            raise ValueError("verify_predicate must be a callable")
        url = f"{AUTONOMIC_COMMAND_BASE_URL}/{self.vin}/commands"
        json = {
            "type": command,
            "wakeUp": True,
        }
        logger.info('Issuing "%s" command...', command)
        response = self._request("POST", url, json=json)
        logger.info('Command "%s" issued successfully. Allow at least 20 seconds for it to take effect.', command)

        if verify:
            logger.info("Waiting %d seconds before verifying command results...", verify_delay)
            time.sleep(verify_delay)
            if not verify_predicate():
                if "%s" in fail_msg:
                    logger.error(fail_msg, command)
                    raise VehiclePassCommandError(fail_msg % command)
                else:
                    logger.error(fail_msg)
                    raise VehiclePassCommandError(fail_msg)
            if "%s" in success_msg:
                logger.info(success_msg, command)
            else:
                logger.info(success_msg)
        return response

    def auth(self):
        """Authenticate with the VehiclePass API."""
        self._get_fordpass_token()
        self._get_autonomic_token()
        self.http_client.headers.update(
            {
                "User-Agent": FORDPASS_USER_AGENT,
                "Authorization": f"Bearer {self.autonomic_token}",
                "Application-Id": FORDPASS_APPLICATION_ID,
            }
        )

    @property
    def doors(self) -> Doors:
        """Get the door status for all doors.

        Returns:
            Doors object containing status for all doors
        """
        return Doors(self)

    def start(
        self,
        check_shutoff_time: bool = False,
        extend_shutoff_time: bool = False,
        extend_shutoff_time_delay: float | int = 30.0,
        verify: bool = False,
        verify_delay: float | int = 30.0,
        force: bool = False,
    ) -> None:
        """Request remote start.

        Args:
            check_shutoff_time: Whether to check and log the vehicle shutoff time
            extend_shutoff_time: Whether to extend the vehicle shutoff time by 15 minutes
            extend_shutoff_time_delay: Delay in seconds to wait before requesting vehicle shutoff extension
            verify: Whether to verify all commands' success after issuing them
            verify_delay: Delay in seconds to wait before verifying the commands' success
            force: Whether to issue the command even if the vehicle is already running

        """
        if self.is_running and not force:
            logger.info("Vehicle is already running, no command issued. Pass force=True to issue the command anyway.")
            return

        if self.is_running and force:
            logger.info("Vehicle is already running but force flag is enabled, issuing command anyway...")

        self._send_command(
            command="remoteStart",
            verify=verify,
            verify_delay=verify_delay,
            verify_predicate=lambda: self.is_running,
            success_msg="Vehicle is now running",
            fail_msg="Vehicle failed to start",
        )
        if extend_shutoff_time:
            logger.info("Waiting %d seconds before requesting shutoff extension...", extend_shutoff_time_delay)
            time.sleep(extend_shutoff_time_delay)
            self._send_command(
                command="remoteStart",
                verify=verify,
                verify_delay=verify_delay,
                verify_predicate=lambda: self.is_running,
                success_msg="Shutoff time extended successfully",
                fail_msg="Shutoff time extension failed",
            )

        if check_shutoff_time:
            self.refresh_status()
            seconds = self.shutoff_time_seconds
            if seconds is not None:
                shutoff = self.shutoff_time
                logger.info(
                    "Vehicle will shut off at %s local time (in %.0f seconds)",
                    shutoff.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                    seconds,
                )
            else:
                logger.warning("Unable to determine vehicle shutoff time")

    def stop(self, verify: bool = False, verify_delay: float | int = 30.0, force: bool = False) -> None:
        """Stop the vehicle.

        Args:
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success
            force: Whether to issue the command even if the vehicle i already not running

        Returns:
            None
        """
        if self.is_running and not force:
            logger.info("Vehicle is already running, no command issued. Pass force=True to issue the command anyway.")
            return

        if self.is_running and force:
            logger.info("Vehicle is already running but force flag is enabled, issuing command anyway...")

        self._send_command(
            command="cancelRemoteStart",
            verify=verify,
            verify_delay=verify_delay,
            verify_predicate=lambda: self.is_not_running,
            success_msg="Vehicle's engine is now stopped",
            fail_msg="Vehicle's engine failed to stop",
        )

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
    def fuel_level(self) -> float:
        """Get the fuel level as a percentage."""
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
        return Distance.from_kilometers(value)

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
        return Indicators(self._get_metric_value("indicators", dict))

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
        return Distance.from_miles(value)

    @property
    def outside_temp(self) -> Temperature:
        """Get the outside temperature using the configured unit preferences.

        Returns:
            The outside temperature as a Temperature object.
        """
        value = self._get_metric_value("outsideTemperature", float)
        if value is None:
            return None
        return Temperature.from_celsius(value)

    def refresh_status(self) -> None:
        """Refresh the vehicle status data."""
        self._status = self._request("GET", f"{AUTONOMIC_TELEMETRY_BASE_URL}/{self.vin}")

    @property
    def shutoff_time(self) -> datetime.datetime:
        """Get the vehicle shutoff time."""
        return datetime.datetime.fromtimestamp(self.shutoff_time_seconds)

    @property
    def shutoff_time_seconds(self) -> float:
        """Get the vehicle shutoff time in seconds since epoch."""
        return self._get_metric_value("shutoffTime", float)

    @property
    def status(self) -> dict:
        """Get the vehicle status."""
        if not self._status:
            self.refresh_status()
        return self._status

    @property
    def tire_pressure(self) -> TirePressure:
        """Get the tire pressure readings.

        Raises:
            VehiclePassStatusError: If tire pressure data is not available
        """
        return TirePressure(self._get_metric_value("tirePressure", list))
