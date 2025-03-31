"""Door status readings for all vehicle doors."""

from typing import TYPE_CHECKING, Any

from vehiclepass.errors import VehiclePassStatusError

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle


class Doors:
    """Represents door status readings for all vehicle doors."""

    def __init__(self, vehicle: "Vehicle", status_data: list[dict[str, Any]]) -> None:
        """Initialize door status readings from status data and dynamically create properties.

        Args:
            status_data: List of door status readings from status JSON

        Raises:
            VehiclePassStatusError: If status_data is None or empty
        """
        self._vehicle = vehicle
        if not status_data:
            raise VehiclePassStatusError("status_data cannot be None or empty")
        self._status_data = status_data
        self._data = {}

        for door in status_data:
            door_position = door.get("vehicleDoor", "").lower()
            if not door_position or "value" not in door:
                continue

            # Store door status values
            self._data[door_position] = door["value"]

            # Create property getter for each door
            def make_getter(pos):
                def getter(self) -> str:
                    """Get door status.

                    Returns:
                        Door status value
                    """
                    return self._data.get(pos)

                return getter

            # Skip ALL_DOORS as it's handled separately
            if door_position != "all_doors":
                setattr(Doors, door_position, property(make_getter(door_position)))

    def get_status(self, door_position: str) -> str | None:
        """Get status for a specific door.

        Args:
            door_position: Door position identifier (e.g., 'front_left')

        Returns:
            Door status value, or None if position not found
        """
        return self._data.get(door_position.lower())

    def __repr__(self) -> str:
        """Return string representation showing available door positions."""
        positions = list(self._data.keys())
        return f"DoorStatus(doors={positions})"
