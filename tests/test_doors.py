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
    assert hasattr(vehicle.doors, "unspecified_front")
    assert hasattr(vehicle.doors, "front_left")
    assert hasattr(vehicle.doors, "front_right")
    assert hasattr(vehicle.doors, "rear_left")
    assert hasattr(vehicle.doors, "rear_right")
    assert hasattr(vehicle.doors, "tailgate")
    assert hasattr(vehicle.doors, "inner_tailgate")
    assert vehicle.doors.front_left == "CLOSED"
    assert vehicle.doors.front_right == "CLOSED"
    assert vehicle.doors.rear_left == "CLOSED"  # type: ignore
    assert vehicle.doors.rear_right == "CLOSED"  # type: ignore
    assert vehicle.doors.tailgate == "CLOSED"  # type: ignore
    assert vehicle.doors.inner_tailgate == "CLOSED"  # type: ignore


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
