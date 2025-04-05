"""Test vehicle commands."""

import pytest

import vehiclepass

from .conftest import mock_responses


@mock_responses(
    status=[
        "status/baseline.json",
        "status/remotely_started.json",
    ],
    commands={
        "remoteStart": "commands/remote_start.json",
    },
)
def test_command_success(vehicle: vehiclepass.Vehicle):
    """Test command success."""
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle._remote_start_count == 0

    result = vehicle._send_command(
        "remoteStart",
        check_predicate=lambda: vehicle.is_not_running,
        verify_predicate=lambda: vehicle.is_remotely_started,
        verify_delay=0.001,
        success_msg="Vehicle is now running.",
        not_issued_msg="Vehicle is already running, no command issued.",
    )
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle.is_not_ignition_started
    assert result is not None
    assert result["currentStatus"] == "REQUESTED"
    assert result["statusReason"] == "Command in progress"


@mock_responses(
    status=[
        "status/baseline.json",
    ],
    commands={
        "remoteStart": "commands/remote_start.json",
    },
)
def test_command_failure(vehicle: vehiclepass.Vehicle):
    """Test command failure."""
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle._remote_start_count == 0

    # Fails because status returned is baseline.json, which does not indicate a remotely started vehicle.
    with pytest.raises(vehiclepass.CommandError):
        vehicle._send_command(
            "remoteStart",
            check_predicate=lambda: vehicle.is_not_running,
            verify_predicate=lambda: vehicle.is_remotely_started,
            verify_delay=0.001,
            success_msg="Vehicle is now running.",
            not_issued_msg="Vehicle is already running, no command issued.",
        )
