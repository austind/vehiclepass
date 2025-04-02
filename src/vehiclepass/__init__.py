"""An experimental Python client for the VehiclePass API."""

import os

from dotenv import load_dotenv

from vehiclepass.errors import CommandError, StatusError
from vehiclepass.vehicle import Vehicle

load_dotenv()


def vehicle(
    username: str = os.getenv("FORDPASS_USERNAME", ""),
    password: str = os.getenv("FORDPASS_PASSWORD", ""),
    vin: str = os.getenv("FORDPASS_VIN", ""),
) -> Vehicle:
    """Create a Vehicle instance."""
    return Vehicle(username, password, vin)


__all__ = ["CommandError", "StatusError", "Vehicle", "vehicle"]
