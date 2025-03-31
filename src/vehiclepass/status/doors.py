"""Door status readings for all vehicle doors."""

import logging
import time
from typing import TYPE_CHECKING

from vehiclepass.errors import VehiclePassCommandError, VehiclePassStatusError

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle

logger = logging.getLogger(__name__)


class Doors:
    """Represents door status readings for all vehicle doors."""

    def __init__(self, vehicle: "Vehicle") -> None:
        """Initialize door status readings from status data and dynamically create properties.

        Args:
            vehicle: Parent vehicle object

        Raises:
            VehiclePassStatusError: If status_data is None or empty
        """
        self._vehicle = vehicle
        self._doors = {}
        self._door_status = {}
        try:
            self.door_status = self._vehicle.status.raw["metrics"]["doorStatus"]
        except KeyError:
            raise VehiclePassStatusError("Door status not found in vehicle status metrics")

        for door in self.door_status:
            door_position = door.get("vehicleDoor", "").lower()
            self._doors[door_position] = door["value"]

            # Skip ALL_DOORS as it's handled separately
            if door_position != "all_doors":
                setattr(self, door_position, door["value"])

    @property
    def are_locked(self) -> bool:
        """Check if all doors are locked."""
        try:
            lock_status = next(
                x for x in self._vehicle.status.raw["metrics"]["doorLockStatus"] if x["vehicleDoor"] == "ALL_DOORS"
            )
        except KeyError | StopIteration:
            raise VehiclePassStatusError("Door lock status not found in vehicle status metrics")

        return lock_status.get("value", "").lower() == "locked"

    @property
    def are_unlocked(self) -> bool:
        """Check if all doors are unlocked."""
        return not self.are_locked

    def lock(self, verify: bool = False, verify_delay: float | int = 20.0) -> None:
        """Lock the vehicle."""
        logger.info("Issuing lock command...")
        self._vehicle._send_command("lock")
        logger.info("Lock command issued successfully")
        if verify:
            logger.info("Waiting %d seconds before verifying lock command...", verify_delay)
            time.sleep(verify_delay)
            self._vehicle.status.refresh()
            if not self.are_unlocked:
                msg = "Lock command issued successfully, but doors did not lock"
                logger.error(msg)
                raise VehiclePassCommandError(msg)
            logger.info("Doors locked successfully")

    def unlock(self, verify: bool = False, verify_delay: float | int = 20.0) -> None:
        """Unlock the vehicle."""
        logger.info("Issuing unlock command...")
        self._vehicle._send_command("unLock")
        logger.info("Unlock command issued successfully")
        if verify:
            logger.info("Waiting %d seconds before verifying unlock command...", verify_delay)
            time.sleep(verify_delay)
            self._vehicle.status.refresh()
            if self.are_locked:
                msg = "Unlock command issued successfully, but doors did not unlock"
                logger.error(msg)
                raise VehiclePassCommandError(msg)
            logger.info("Doors unlocked successfully")

    def __repr__(self) -> str:
        """Return string representation showing available door positions."""
        positions = list(self._doors.keys())
        return f"DoorStatus(doors={positions})"
