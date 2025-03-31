"""Vehicle class."""

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
    COMMAND_DELAY,
    FORDPASS_APPLICATION_ID,
    FORDPASS_AUTH_URL,
    FORDPASS_USER_AGENT,
    LOGIN_USER_AGENT,
)
from vehiclepass.errors import VehiclePassCommandError
from vehiclepass.status import VehicleStatus

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
            raise ValueError(
                "FordPass username (email address), password, and VIN are required"
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

    def start(self, extended: bool = False) -> None:
        """Request remote start."""
        self._send_command("remoteStart")
        logger.info("Remote start requested")
        logger.info(
            "Waiting %d seconds before %s...",
            COMMAND_DELAY,
            "checking vehicle shutoff time"
            if not extended
            else "requesting remote start extension",
        )
        time.sleep(COMMAND_DELAY)

        if extended:
            self._send_command("remoteStart")
            logger.info("Vehicle remote start extension requested")

        self.status.refresh()  # Refresh status before checking shutoff time
        seconds = self.status.shutoff_time_seconds
        if seconds is not None:
            shutoff = self.status.shutoff_time
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

    def stop(self, verify: bool = True, delay: int = COMMAND_DELAY) -> None:
        """Stop the vehicle."""
        if self.status.is_running:
            self._send_command("cancelRemoteStart")
            logger.info(
                "Vehicle shutoff requested%s",
                f". Waiting {delay} seconds to verify..." if verify else ".",
            )
            time.sleep(delay)
            if verify:
                self.status.refresh()  # Refresh status before verifying
                if self.status.is_running:
                    logger.error("Vehicle shutoff failed.")
                    raise VehiclePassCommandError("Vehicle shutoff failed.")
                else:
                    logger.info("Vehicle shutoff successful.")
        else:
            logger.info("Vehicle is not running, no shutoff requested.")
