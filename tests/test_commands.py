"""Test vehicle commands."""

import httpx
import pytest

import vehiclepass

from .conftest import load_mock_json, mock_responses


@mock_responses(
    status=[
        "status/baseline.json",
        "status/remotely_started.json",
    ],
    commands={
        "remoteStart": "commands/remote_start.json",
    },
)
def test_send_command(vehicle: vehiclepass.Vehicle):
    """Test that command responses are correctly loaded from files."""
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
        "status/remotely_started.json",
        "status/baseline.json",
    ],
    commands={
        "remoteStart": "commands/remote_start.json",
        "cancelRemoteStart": "commands/cancel_remote_start.json",
    },
)
def test_start_and_stop(vehicle: vehiclepass.Vehicle):
    """Test vehicle start and stop commands."""
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle._remote_start_count == 0

    vehicle.start(verify=True, verify_delay=0.001)
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle.shutoff_countdown.seconds == 851.0
    assert vehicle.shutoff_countdown.human_readable == "14m 11s"
    assert str(vehicle.shutoff_countdown) == "14m 11s"
    assert vehicle._remote_start_count == 1

    vehicle.stop(verify=True, verify_delay=0.001)
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle.shutoff_countdown.seconds == 0.0
    assert vehicle.shutoff_countdown.human_readable == "0s"
    assert vehicle._remote_start_count == 1


@mock_responses(
    status=[
        "status/baseline.json",
        "status/remotely_started.json",
        "status/remotely_started_extended.json",
    ],
    commands={
        "remoteStart": [
            "commands/remote_start.json",
        ],
    },
)
def test_extend_shutoff(vehicle: vehiclepass.Vehicle):
    """Test extending the shutoff time."""
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle._remote_start_count == 0

    vehicle.start(verify=True, verify_delay=0.001)
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle._remote_start_count == 1

    vehicle.extend_shutoff(verify=True, verify_delay=0.001, delay=0.001)
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle.shutoff_countdown.seconds == 1719.0
    assert vehicle._remote_start_count == 2


@mock_responses(
    status=[
        "status/baseline.json",
        "status/remotely_started.json",
        "status/remotely_started_extended.json",
    ],
    commands={
        "remoteStart": [
            "commands/remote_start.json",
            "commands/remote_start.json",
            httpx.Response(status_code=403, json=load_mock_json("commands/remote_start_forbidden.json")),
        ],
    },
)
def test_exceed_max_start_count(vehicle: vehiclepass.Vehicle):
    """Test exceeding the maximum number of remote starts."""
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle._remote_start_count == 0

    vehicle.start(verify=True, verify_delay=0.001)
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle._remote_start_count == 1

    vehicle.extend_shutoff(verify=True, verify_delay=0.001, delay=0.001)
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle.shutoff_countdown.seconds == 1719.0
    assert vehicle._remote_start_count == 2

    # Without force=True, the command shouldn't run.
    vehicle.extend_shutoff(verify=True, verify_delay=0.001, delay=0.001)
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle.shutoff_countdown.seconds == 1719.0
    assert vehicle._remote_start_count == 2

    # With force=True, the command should fail, as the FordPass API only allows 2 remote starts
    # before the vehicle must be manually started.
    with pytest.raises(httpx.HTTPStatusError) as exc:
        vehicle.extend_shutoff(verify=True, verify_delay=0.001, delay=0.001, force=True)
        assert exc.value.response.status_code == 403
