"""Test vehicle commands."""

from vehiclepass import Vehicle

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
def test_command_responses(vehicle: Vehicle):
    """Test that command responses are correctly loaded from files."""
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle._remote_start_count == 0

    result = vehicle._send_command(
        "remoteStart", verify=True, check_predicate=lambda: vehicle.is_remotely_started, verify_delay=0.1
    )
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle.is_not_ignition_started
    # TODO: Need to fix this
    # assert vehicle._remote_start_count == 1
    assert result is not None
    assert result["currentStatus"] == "REQUESTED"
    assert result["statusReason"] == "Command in progress"


@mock_responses(
    status=[
        "status/baseline.json",
        "status/remotely_started.json",
        "status/baseline.json",
    ],
    commands={
        "remoteStart": "commands/remote_start.json",
        "cancelRemoteStart": "commands/cancel_remote_start.json",
    },
)
def test_start_and_stop(vehicle: Vehicle):
    """Test vehicle start and stop commands."""
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle._remote_start_count == 0

    vehicle.start(verify=True, verify_delay=0.1)
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle.shutoff_countdown.seconds == 1719.0
    assert vehicle.shutoff_countdown.human_readable == "29m 39s"
    assert str(vehicle.shutoff_countdown) == "29m 39s"
    assert vehicle._remote_start_count == 1

    vehicle.stop(verify=True, verify_delay=0.1)
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle.shutoff_countdown.seconds == 0.0
    assert vehicle.shutoff_countdown.human_readable == "0s"
    assert vehicle._remote_start_count == 1
