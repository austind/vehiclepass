"""Vehicle class."""

import datetime
import json
import logging
import os
import time
from collections.abc import Callable
from typing import Any, Optional, TypeVar, Union

import httpx
from dotenv import load_dotenv
from pydantic import NonNegativeInt

from vehiclepass._types import AlarmStatus, CompassDirection, GearLeverPosition, HoodStatus, VehicleCommand
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
from vehiclepass.errors import CommandError, StatusError
from vehiclepass.indicators import Indicators
from vehiclepass.tire_pressure import TirePressure
from vehiclepass.units import Distance, Duration, ElectricPotential, Percentage, Temperature

load_dotenv()

logger = logging.getLogger(__name__)


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
        self.http_client = httpx.Client()
        self.http_client.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": "en-US",
                "Accept-Encoding": "gzip, deflate, br",
            }
        )
        self._status: dict[str, Any] = {}
        self._fordpass_token = None
        self._autonomic_token = None
        self._remote_start_count = 0

    def __enter__(self) -> "Vehicle":
        """Enter the context manager."""
        self.auth()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        self.http_client.close()

    def _get_autonomic_token(self) -> None:
        """Get an Autonomic token."""
        data = {
            "subject_token": self._fordpass_token,
            "subject_issuer": "fordpass",
            "client_id": "fordpass-prod",
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        }
        result = self._request("POST", AUTONOMIC_AUTH_URL, data=data)
        self._autonomic_token = result["access_token"]
        logger.info("Obtained Autonomic token")

    def _get_fordpass_token(self) -> None:
        """Get a FordPass token."""
        self.http_client.headers["User-Agent"] = LOGIN_USER_AGENT

        json = {
            "username": self.username,
            "password": self.password,
        }
        result = self._request("POST", FORDPASS_AUTH_URL, json=json)
        self._fordpass_token = result["access_token"]
        logger.info("Obtained FordPass token")

    def _get_metric_value(self, metric_name: str, expected_type: Optional[type[T]] = None) -> T:
        """Get a value from the metrics dictionary with error handling.

        Args:
            metric_name: The name of the metric to retrieve
            expected_type: The expected type of the value (optional)

        Returns:
            The metric value, rounded to 2 decimal places if numeric

        Raises:
            StatusError: If the metric is not found or invalid
        """
        try:
            metric = self.status.get("metrics", {}).get(metric_name, {})
            if not metric:
                raise StatusError(f"{metric_name} not found in metrics")

            # If metric has a value key, use it, otherwise use the metric itself
            # e.g. tirePressure is a list of dictionaries, each with a value key
            if "value" in metric:
                value = metric["value"]
            else:
                value = metric

            if expected_type is not None and not isinstance(value, expected_type):
                raise StatusError(f"Invalid {metric_name} type")
            return value  # type: ignore
        except Exception as exc:
            if isinstance(exc, StatusError):
                raise
            raise StatusError(f"Error getting {metric_name}: {exc!s}") from exc

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

    def _send_command(
        self,
        command: VehicleCommand,
        check_predicate: Optional[Callable] = None,
        verify_predicate: Optional[Callable] = None,
        verify_delay: Union[float, int] = 30.0,
        success_msg: str = 'Command "%s" completed successfully',
        fail_msg: str = 'Command "%s" failed to complete',
        force: bool = False,
        not_issued_msg: str = 'Command "%s" not issued. Pass force=True to issue the command anyway.',
        forced_msg: str = 'Force flag is enabled, command "%s" issued anyway',
    ) -> Optional[dict]:
        """Send a command to the vehicle.

        This method sends a specified command to the vehicle and optionally verifies its success.
        It handles command issuance, logging, and error management.

        Args:
            command: The command to send, represented as a `VehicleCommand`.
            check_predicate: A callable that checks if the command should be issued. If None, the command will be
                issued unconditionally.
            verify_predicate: A callable that checks if the command was successful. If None, no verification
                will be attempted.
            verify_delay: The delay in seconds to wait before verifying the command's success.
            success_msg: The message to log if the command succeeds. If "%s" is present, it will be
                replaced with the value passed in `command`.
            fail_msg: The message to log if the command fails. If "%s" is present, it will be replaced
                with the value passed in `command`.
            force: A boolean indicating whether to issue the command even if the vehicle's state does not
                require it (check_predicate() evaluates to False). Has no effect if check_predicate is None.
            not_issued_msg: The message to log if the command is not issued due to the vehicle's state.
            forced_msg: The message to log if the command is issued despite the vehicle's state.

        Returns:
            dict: The response from the command, typically containing the result of the command execution.

        Raises:
            ValueError: If `verify` is True but `check_predicate` is None, or if `force` is True but
            `check_predicate` is None.
            CommandError: If the command fails to complete successfully after verification.
        """
        if check_predicate is not None and bool(check_predicate()) is False:
            if force:
                if "%s" in forced_msg:
                    logger.info(forced_msg, command)
                else:
                    logger.info(forced_msg)
            else:
                if "%s" in not_issued_msg:
                    logger.info(not_issued_msg, command)
                else:
                    logger.info(not_issued_msg)
                return None

        url = f"{AUTONOMIC_COMMAND_BASE_URL}/{self.vin}/commands"
        json = {
            "type": command,
            "wakeUp": True,
        }
        logger.info('Issuing "%s" command...', command)
        try:
            response = self._request("POST", url, json=json)
        except httpx.HTTPStatusError as exc:
            raise CommandError(
                f'Command "{command}" failed to execute, status {exc.response.status_code}', response=exc.response
            ) from exc

        refresh_reminder = ", and call refresh_status() afterward." if not verify_predicate and not force else "."
        logger.info(
            'Command "%s" issued successfully. Allow at least 20 seconds for it to take effect%s',
            command,
            refresh_reminder,
        )

        if verify_predicate is not None:
            logger.info("Waiting %d seconds before verifying command results...", verify_delay)
            time.sleep(verify_delay)
            self.refresh_status()
            if bool(verify_predicate()) is not True:
                if "%s" in fail_msg:
                    logger.error(fail_msg, command)
                    raise CommandError(fail_msg % command)
                else:
                    logger.error(fail_msg)
                    raise CommandError(fail_msg)
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
                "Authorization": f"Bearer {self._autonomic_token}",
                "Application-Id": FORDPASS_APPLICATION_ID,
            }
        )

    def extend_shutoff(
        self,
        verify: bool = False,
        verify_delay: Union[float, int] = 30.0,
        force: bool = False,
        delay: Union[float, int] = 30.0,
    ) -> None:
        """Extend the vehicle shutoff time by 15 minutes.

        Args:
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success
            force: Whether to issue the command even if the vehicle's shutoff time is already extended
            delay: Delay in seconds to wait before issuing the command
        Returns:
            None
        """
        if not self.is_running:
            if force:
                logger.info(
                    "Vehicle is not running, but force flag enabled, issuing shutoff extension command anyway..."
                )
            else:
                logger.info("Vehicle is not running, shutoff extension command not issued.")
                return

        if self._remote_start_count >= 2:
            if force:
                logger.info(
                    "Vehicle has already been issued the maximum 2 remote start requests, "
                    "but force flag enabled, issuing shutoff extension command anyway..."
                )
            else:
                logger.info(
                    "Vehicle has already been issued the maximum 2 remote start requests, "
                    "shutoff extension command not issued."
                )
                return

        if delay:
            logger.info("Waiting %d seconds before requesting shutoff extension...", delay)
            time.sleep(delay)

        self._send_command(
            command="remoteStart",
            verify_delay=verify_delay,
            check_predicate=lambda: self.is_running,
            verify_predicate=lambda: self.shutoff_countdown.seconds > 900.0,
            success_msg="Shutoff time extended successfully",
            fail_msg="Shutoff time extension failed",
            force=force,
            not_issued_msg="Vehicle is not running, no command issued. First issue vehicle.start().",
            forced_msg="Vehicle is already running but force flag enabled, issuing command anyway...",
        )
        self._remote_start_count += 1

    def refresh_status(self) -> None:
        """Refresh the vehicle status data."""
        self._status = self._request("GET", f"{AUTONOMIC_TELEMETRY_BASE_URL}/{self.vin}")

    def start(
        self,
        extend_shutoff: bool = False,
        extend_shutoff_delay: Union[float, int] = 30.0,
        verify: bool = True,
        verify_delay: Union[float, int] = 30.0,
        force: bool = False,
    ) -> None:
        """Request remote start.

        Each remote start request adds 15 minutes to the vehicle's shutoff time. The FordPass API allows for two remote
        start requests before you must manually start the vehicle.

        Args:
            extend_shutoff: Whether to extend the vehicle shutoff time by 15 minutes, for a total of 30 minutes.
                This simply issues two `remoteStart` commands in succession.
            extend_shutoff_delay: Delay in seconds to wait before requesting vehicle shutoff extension.
            verify: Whether to verify all commands' success after issuing them.
            verify_delay: Delay in seconds to wait before verifying the commands' success.
            force: Whether to issue the commands, even if they are not necessary or if the maximum number of remote
                start requests (2) has already been issued.

        Returns:
            None
        """
        if self._send_command(
            command="remoteStart",
            verify_delay=verify_delay,
            check_predicate=lambda: self.is_not_running if verify else None,
            verify_predicate=lambda: self.is_remotely_started,
            success_msg="Vehicle is now running",
            fail_msg="Vehicle failed to start",
            force=force,
            not_issued_msg="Vehicle is already running, no command issued",
            forced_msg="Vehicle is already running but force flag enabled, issuing command anyway...",
        ):
            self._remote_start_count += 1
            if extend_shutoff:
                self.extend_shutoff(verify_delay=verify_delay, force=force, delay=extend_shutoff_delay)

            if verify:
                if shutoff := self.shutoff_time:
                    logger.info(
                        "Vehicle will shut off at %s local time (in %.0f seconds)",
                        shutoff.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                        self.shutoff_countdown.seconds,
                    )
                else:
                    logger.warning("Unable to determine vehicle shutoff time")

    def stop(self, verify: bool = True, verify_delay: Union[float, int] = 30.0, force: bool = False) -> None:
        """Shut off the engine.

        Args:
            verify: Whether to verify the command's success after issuing it.
            verify_delay: Delay in seconds to wait before verifying the command's success.
            force: Whether to issue the command even if the vehicle is already shut off.

        Returns:
            None
        """
        self._send_command(
            command="cancelRemoteStart",
            verify_delay=verify_delay,
            check_predicate=lambda: self.is_running,
            verify_predicate=lambda: self.is_not_running if verify else None,
            force=force,
            success_msg="Vehicle's engine is now stopped",
            fail_msg="Vehicle's engine failed to stop",
            not_issued_msg="Vehicle is already stopped, no command issued",
            forced_msg="Vehicle is already stopped but force flag enabled, issuing command anyway...",
        )

    @property
    def alarm_status(self) -> AlarmStatus:
        """Get the alarm status."""
        return self._get_metric_value("alarmStatus")

    @property
    def battery_charge(self) -> Percentage:
        """Get the battery charge percentage."""
        return Percentage(self._get_metric_value("batteryStateOfCharge", float) / 100)

    @property
    def battery_voltage(self) -> ElectricPotential:
        """Get the battery voltage."""
        return ElectricPotential.from_volts(self._get_metric_value("batteryVoltage", float))

    @property
    def compass_direction(self) -> CompassDirection:
        """Get the compass direction."""
        return self._get_metric_value("compassDirection")

    @property
    def doors(self) -> Doors:
        """Get the door status for all doors."""
        return Doors(self)

    @property
    def engine_coolant_temp(self) -> Temperature:
        """Get the engine coolant temperature."""
        return Temperature.from_celsius(self._get_metric_value("engineCoolantTemp", float))

    @property
    def fuel_level(self) -> Percentage:
        """Get the fuel level as a percentage."""
        return Percentage(self._get_metric_value("fuelLevel", float) / 100)

    @property
    def fuel_range(self) -> Distance:
        """Get the fuel range using the configured unit preferences."""
        return Distance.from_kilometers(self._get_metric_value("fuelRange", float))

    @property
    def gear_lever_position(self) -> GearLeverPosition:
        """Get the gear lever position."""
        return self._get_metric_value("gearLeverPosition")

    @property
    def hood_status(self) -> HoodStatus:
        """Get the hood status."""
        return self._get_metric_value("hoodStatus")

    @property
    def indicators(self) -> Indicators:
        """Get the vehicle indicators status."""
        return Indicators(self)

    @property
    def is_ignition_started(self) -> bool:
        """Check if the vehicle's ignition is on (started manually from within the vehicle)."""
        return self._get_metric_value("ignitionStatus", str) == "ON"

    @property
    def is_not_ignition_started(self) -> bool:
        """Check if the vehicle's ignition is off (not started manually from within the vehicle)."""
        return self._get_metric_value("ignitionStatus", str) == "OFF"

    @property
    def is_not_remotely_started(self) -> bool:
        """Check if the vehicle is not running from a remote start command, but not from the ignition."""
        return not self.is_remotely_started

    @property
    def is_not_running(self) -> bool:
        """Check if the vehicle is not running, either from the ignition or a remote start command."""
        return self.is_not_ignition_started and self.is_not_remotely_started

    @property
    def is_remotely_started(self) -> bool:
        """Check if the vehicle is running from a remote start command, but not from the ignition."""
        try:
            remote_start_status = self.status["events"]["remoteStartEvent"]
            return (
                "remoteStartBegan" in remote_start_status["conditions"]
                and remote_start_status["conditions"]["remoteStartBegan"]["remoteStartDeviceStatus"]["value"]
                == "RUNNING"
            )
        except KeyError as exc:
            raise StatusError("Unable to determine if vehicle is remotely started.") from exc

    @property
    def is_running(self) -> bool:
        """Check if the vehicle is running, either from the ignition or a remote start command."""
        return self.is_ignition_started or self.is_remotely_started

    @property
    def odometer(self) -> Distance:
        """Get the odometer reading."""
        return Distance.from_kilometers(self._get_metric_value("odometer", float))

    @property
    def outside_temp(self) -> Temperature:
        """Get the outside temperature using the configured unit preferences.

        Returns:
            The outside temperature as a Temperature object.
        """
        return Temperature.from_celsius(self._get_metric_value("outsideTemperature", float))

    @property
    def rpm(self) -> NonNegativeInt:
        """Get the engine's current RPM."""
        return self._get_metric_value("engineSpeed", int)

    @property
    def shutoff_countdown(self) -> Duration:
        """Get the vehicle shutoff time in seconds."""
        return Duration.from_seconds(self._get_metric_value("remoteStartCountdownTimer", float))

    @property
    def shutoff_time(self) -> Optional[datetime.datetime]:
        """Get the vehicle shutoff time."""
        if self.shutoff_countdown.seconds == 0.0:
            return None
        return datetime.datetime.now() + datetime.timedelta(seconds=self.shutoff_countdown.seconds)

    @property
    def status(self) -> dict:
        """Get the vehicle status."""
        if not self._status:
            self.refresh_status()
        return self._status

    @property
    def tire_pressure(self) -> TirePressure:
        """Get the tire pressure readings."""
        return TirePressure(self)
