"""Door status readings for all vehicle doors."""

from typing import Any

from vehiclepass.errors import VehiclePassStatusError


class DoorStatus:
    """Represents door status readings for all vehicle doors."""

    def __init__(self, door_status_data: list[dict[str, Any]]) -> None:
        """Initialize door status readings from status data and dynamically create properties.

        Args:
            door_status_data: List of door status readings from status JSON

        Raises:
            VehiclePassStatusError: If door_status_data is None or empty
        """
        if not door_status_data:
            raise VehiclePassStatusError("door_status_data cannot be None or empty")

        self._data = {}

        for door in door_status_data:
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
                setattr(DoorStatus, door_position, property(make_getter(door_position)))

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
