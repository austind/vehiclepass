"""Vehicle class."""

import json
import logging
import os
import time
from collections.abc import Callable

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
from vehiclepass.errors import VehiclePassCommandError
from vehiclepass.status import VehicleStatus
from vehiclepass.status.doors import Doors

load_dotenv()

logger = logging.getLogger(__name__)


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
        self._status = None

    def __enter__(self) -> "Vehicle":
        """Enter the context manager."""
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        self.http_client.close()

    def login(self):
        """Login to the VehiclePass API."""
        self._get_fordpass_token()
        self._get_autonomic_token()
        self.http_client.headers.update(
            {
                "User-Agent": FORDPASS_USER_AGENT,
                "Authorization": f"Bearer {self.autonomic_token}",
                "Application-Id": FORDPASS_APPLICATION_ID,
            }
        )

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

    @property
    def telemetry_url(self) -> str:
        """Get the telemetry base URL."""
        return AUTONOMIC_TELEMETRY_BASE_URL

    @property
    def status(self) -> VehicleStatus:
        """Get the vehicle status."""
        if self._status is None:
            self._status = VehicleStatus(self)
        return self._status

    def _send_command(
        self,
        command: str,
        verify: bool = False,
        verify_delay: float | int = 20.0,
        verify_predicate: Callable | None = None,
        success_msg: str = "Command %s completed successfully",
        fail_msg: str = "Command %s issued successfully, but did not complete",
    ) -> dict:
        """Send a command to the vehicle."""
        if verify and not verify_predicate:
            raise ValueError("verify_predicate is required if verify is True")
        if not callable(verify_predicate):
            raise ValueError("verify_predicate must be a callable")
        url = f"{AUTONOMIC_COMMAND_BASE_URL}/{self.vin}/commands"
        json = {
            "type": command,
            "wakeUp": True,
        }
        logger.info("Issuing command %s...", command)
        response = self._request("POST", url, json=json)
        logger.info("Command %s issued successfully", command)
        if verify:
            logger.info("Waiting %d seconds before verifying command results...", verify_delay)
            time.sleep(verify_delay)
            if not verify_predicate():
                logger.error(fail_msg, command)
                raise VehiclePassCommandError(fail_msg % command)
        logger.info(success_msg, command)
        return response

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
        extend_shutoff_time_delay: float | int = 20.0,
        verify: bool = False,
        verify_delay: float | int = 20.0,
    ) -> None:
        """Request remote start.

        Args:
            check_shutoff_time: Whether to check and log the vehicle shutoff time
            extend_shutoff_time: Whether to extend the vehicle shutoff time by 15 minutes
            extend_shutoff_time_delay: Delay in seconds to wait before requesting vehicle shutoff extension
            verify: Whether to verify all commands' success after issuing them
            verify_delay: Delay in seconds to wait before verifying the commands' success
        """
        if self.status.is_running:
            logger.info("Vehicle is already running, no remote start requested")
            return
        self._send_command(
            command="remoteStart",
            verify=verify,
            verify_delay=verify_delay,
            verify_predicate=lambda: self.status.is_running,
        )
        logger.info("Remote start requested successfully")
        if extend_shutoff_time:
            logger.info("Waiting %d seconds before requesting shutoff extension...", extend_shutoff_time_delay)
            time.sleep(extend_shutoff_time_delay)
            self._send_command(
                command="remoteStart",
                verify=verify,
                verify_delay=verify_delay,
                verify_predicate=lambda: self.status.is_running,
            )
            logger.info("Shutoff extension requested successfully")

        if check_shutoff_time:
            self.status.refresh()
            seconds = self.status.shutoff_time_seconds
            if seconds is not None:
                shutoff = self.status.shutoff_time
                logger.info(
                    "Vehicle will shut off at %s local time (in %.0f seconds)",
                    shutoff.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                    seconds,
                )
            else:
                logger.warning("Unable to determine vehicle shutoff time")

    def stop(self, verify: bool = False, verify_delay: float | int = 20.0) -> None:
        """Stop the vehicle.

        Args:
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success

        Returns:
            None
        """
        if self.status.is_running:
            self._send_command(
                command="cancelRemoteStart",
                verify=verify,
                verify_delay=verify_delay,
                verify_predicate=lambda: self.status.is_not_running,
            )
        else:
            logger.info("Vehicle is not running, no shutoff requested")
