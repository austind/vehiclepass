"""Test vehicle doors."""

import vehiclepass
from vehiclepass.doors import Doors

from .conftest import mock_responses


@mock_responses(status="status/unlocked.json")
def test_doors_closed(vehicle: vehiclepass.Vehicle) -> None:
    """Test doors properties."""
    assert isinstance(vehicle.doors, Doors)
    assert vehicle.doors.are_unlocked
    assert vehicle.doors.are_locked is False
    # We call these with getattr to avoid mypy errors, as doors are dynamically
    # created in the Doors class.
    assert getattr(vehicle.doors, "front_left") == "CLOSED"  # noqa: B009
    assert getattr(vehicle.doors, "front_right") == "CLOSED"  # noqa: B009
    assert getattr(vehicle.doors, "rear_left") == "CLOSED"  # noqa: B009
    assert getattr(vehicle.doors, "rear_right") == "CLOSED"  # noqa: B009
    assert getattr(vehicle.doors, "tailgate") == "CLOSED"  # noqa: B009
    assert getattr(vehicle.doors, "inner_tailgate") == "CLOSED"  # noqa: B009


@mock_responses(
    status=[
        "status/unlocked.json",
        "status/locked.json",
        "status/unlocked.json",
    ],
    commands={
        "lock": "commands/lock.json",
        "unlock": "commands/unlock.json",
    },
)
def test_lock_unlock(vehicle: vehiclepass.Vehicle):
    """Test vehicle lock and unlock methods."""
    assert vehicle.doors.are_unlocked
    vehicle.doors.lock(verify=True, verify_delay=0.01)
    assert vehicle.doors.are_locked
    vehicle.doors.unlock(verify=True, verify_delay=0.01)
    assert vehicle.doors.are_unlocked
