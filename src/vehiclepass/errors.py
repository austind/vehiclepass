"""Errors."""


class VehiclePassError(Exception):
    """Base exception for VehiclePass errors."""

    pass


class CommandError(VehiclePassError):
    """Exception for errors when sending commands to the vehicle."""

    pass


class StatusError(VehiclePassError):
    """Exception for errors when getting the vehicle status."""

    pass
