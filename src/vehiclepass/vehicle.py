"""Vehicle class."""

import datetime
import json
import logging
import os
import time

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
from vehiclepass.errors import VehiclePassStatusError

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
        if not username or not password:
            raise ValueError(
                "FordPass username (email address) and password are required"
            )
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
    def status(self) -> dict:
        """Get the status of the vehicle."""
        url = f"{AUTONOMIC_TELEMETRY_BASE_URL}/{self.vin}"
        return self._request("GET", url)

    def _send_command(self, command: str) -> dict:
        """Send a command to the vehicle."""
        url = f"{AUTONOMIC_COMMAND_BASE_URL}/{self.vin}/commands"
        json = {
            "type": command,
            "wakeUp": True,
        }
        return self._request("POST", url, json=json)

    def lock(self) -> None:
        """Lock the vehicle."""
        self._send_command("lock")

    def unlock(self) -> None:
        """Unlock the vehicle."""
        self._send_command("unLock")

    @property
    def is_locked(self) -> bool:
        """Check if the vehicle is locked."""
        try:
            status = self.status()
            if not isinstance(status, dict) or "metrics" not in status:
                raise VehiclePassStatusError("Invalid status response format")

            door_lock_status = status["metrics"].get("doorLockStatus")
            if not door_lock_status:
                raise VehiclePassStatusError("No door lock status found in metrics")

            all_doors_status = next(
                (x for x in door_lock_status if x.get("vehicleDoor") == "ALL_DOORS"),
                None,
            )
            if not all_doors_status or "value" not in all_doors_status:
                raise VehiclePassStatusError(
                    "Door lock status not found in status response"
                )

            return all_doors_status["value"] == "LOCKED"

        except Exception as e:
            if isinstance(e, VehiclePassStatusError):
                raise
            raise VehiclePassStatusError(f"Error checking lock status: {e!s}") from e

    @property
    def is_unlocked(self) -> bool:
        """Check if the vehicle is unlocked."""
        return not self.is_locked

    @property
    def shutoff_time_seconds(self) -> float | None:
        """Get the number of seconds remaining until vehicle shutoff.

        Returns None if the countdown timer is not available or invalid.
        """
        try:
            countdown_seconds = (
                self.status.get("metrics", {})
                .get("remoteStartCountdownTimer", {})
                .get("value")
            )
            if (
                countdown_seconds is None
                or not isinstance(countdown_seconds, (int | float))
                or countdown_seconds < 0
            ):
                logger.warning("Invalid or missing countdown timer value")
                return None
            return float(countdown_seconds)
        except Exception as e:
            logger.error(f"Error getting shutoff time seconds: {e}")
            return None

    @property
    def shutoff_time(self) -> datetime.datetime | None:
        """Get the UTC time when the vehicle will shut off.

        Returns None if the countdown timer is not available or invalid.
        """
        seconds = self.shutoff_time_seconds
        if seconds is None:
            return None
        return datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=seconds)

    def start(self, extended: bool = False) -> None:
        """Request remote start.

        Defaults to a 15 minute remote start.

        Args:
            extended: Whether to request an extended remote start. If True, will
                request an extension of the remote start by 15 minutes. If successful,
                the vehicle will shut off after 30 minutes.
        """
        self._send_command("remoteStart")
        logger.info("Remote start requested")
        logger.info(
            "Waiting 10 seconds before %s...",
            "checking vehicle shutoff time"
            if not extended
            else "requesting remote start extension",
        )
        time.sleep(10)

        if extended:
            self._send_command("remoteStart")
            logger.info("Vehicle remote start extension requested")

        seconds = self.shutoff_time_seconds
        if seconds is not None:
            shutoff = self.shutoff_time
            logger.info(
                "%sVehicle will shut off at %s local time (in %.0f seconds)",
                "Extended: " if extended else "",
                shutoff.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                seconds,
            )
        else:
            logger.warning(
                "Unable to determine %sshutoff time" % ("extended " if extended else "")
            )

    @property
    def is_running(self) -> bool:
        """Check if the vehicle is running.

        Returns:
            bool: True if the vehicle is running.
        """
        ignition_status = self.status["metrics"].get("ignitionStatus")
        if not ignition_status or "value" not in ignition_status:
            raise VehiclePassStatusError("No ignition status found in metrics")

        return ignition_status["value"] == "ON"
