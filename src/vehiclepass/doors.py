"""Door status readings for all vehicle doors."""

import logging
from typing import TYPE_CHECKING

from vehiclepass.errors import StatusError

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle

logger = logging.getLogger(__name__)


class Doors:
    """Represents vehicle doors."""

    def __init__(self, vehicle: "Vehicle") -> None:
        """Initialize door status readings from status data and dynamically create properties.

        Args:
            vehicle: Parent vehicle object

        Raises:
            StatusError: If status_data is None or empty
        """
        self._vehicle = vehicle
        self._doors = {}
        self._door_status = self._vehicle._get_metric_value("doorStatus", list)

        for door in self._door_status:
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
                x for x in self._vehicle.status["metrics"]["doorLockStatus"] if x["vehicleDoor"] == "ALL_DOORS"
            )
        except (KeyError, StopIteration) as e:
            raise StatusError("Door lock status not found in vehicle status metrics") from e

        return lock_status.get("value", "").lower() == "locked"

    @property
    def are_unlocked(self) -> bool:
        """Check if all doors are unlocked."""
        return not self.are_locked

    def lock(self, verify: bool = True, verify_delay: float | int = 30.0, force: bool = False) -> None:
        """Lock the vehicle.

        Args:
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success
            force: Whether to issue the command even if the vehicle is already locked
        Returns:
            None
        """
        self._vehicle._send_command(
            command="lock",
            force=force,
            verify=verify,
            verify_delay=verify_delay,
            check_predicate=lambda: self.are_locked,
            success_msg="Doors are now locked",
            fail_msg="Doors failed to lock",
            not_issued_msg="Doors are already locked, no command issued",
            forced_msg="Doors are already locked but force flag enabled, issuing command anyway...",
        )

    def unlock(self, verify: bool = True, verify_delay: float | int = 30.0, force: bool = False) -> None:
        """Unlock the vehicle.

        Args:
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success
            force: Whether to issue the command even if the vehicle is already unlocked
        Returns:
            None
        """
        self._vehicle._send_command(
            command="unlock",
            force=force,
            verify=verify,
            verify_delay=verify_delay,
            check_predicate=lambda: self.are_unlocked,
            success_msg="Doors are now unlocked",
            fail_msg="Doors failed to unlock",
            not_issued_msg="Doors are already unlocked, no command issued",
            forced_msg="Doors are already unlocked but force flag enabled, issuing command anyway...",
        )

    def __repr__(self) -> str:
        """Return string representation showing available door positions."""
        positions = list(self._doors.keys())
        return f"DoorStatus(doors={positions})"
