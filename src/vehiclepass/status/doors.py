"""Door status readings for all vehicle doors."""

from typing import TYPE_CHECKING

from vehiclepass.errors import VehiclePassStatusError

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle


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

    def __repr__(self) -> str:
        """Return string representation showing available door positions."""
        positions = list(self._doors.keys())
        return f"DoorStatus(doors={positions})"
