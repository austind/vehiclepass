"""Errors."""


class VehiclePassError(Exception):
    """Base exception for VehiclePass errors."""

    pass


class VehiclePassCommandError(VehiclePassError):
    """Exception for errors when sending commands to the vehicle."""

    pass


class VehiclePassStatusError(VehiclePassError):
    """Exception for errors when getting the vehicle status."""

    pass
