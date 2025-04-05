"""Errors."""

from typing import Optional

import httpx


class VehiclePassError(Exception):
    """Base exception for all vehiclepass errors."""

    pass


class APIError(Exception):
    """Base FordPass API error."""

    def __init__(self, message: str, response: Optional[httpx.Response] = None):
        """Initialize the error."""
        super().__init__(message)
        self.response = response


class CommandError(APIError):
    """Exception raised for errors in command execution."""

    pass


class StatusError(APIError):
    """Exception for errors when getting the vehicle status."""

    pass
