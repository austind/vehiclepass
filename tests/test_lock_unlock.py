"""Test vehicle lock and unlock methods."""

import vehiclepass

from .conftest import mock_responses


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
