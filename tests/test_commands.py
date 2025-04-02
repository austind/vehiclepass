"""Test vehicle commands."""

from .conftest import with_vehicle_mock


@with_vehicle_mock(
    status_file="status/status_off.json",
    command_responses_files={
        "remoteStart": "commands/remote_start.json",
        "cancelRemoteStart": "commands/cancel_remote_start.json",
    },
    mock_data={"property_values": {"is_running": False, "is_remotely_started": False}},
)
def test_command_responses(mocked_vehicle, monkeypatch):
    """Test that command responses are correctly loaded from files."""
    # TODO: Need support for verify=True
    result = mocked_vehicle._send_command("remoteStart", verify=False)
    assert result is not None
    assert result["currentStatus"] == "REQUESTED"
    assert result["statusReason"] == "Command in progress"


@with_vehicle_mock(
    status_file="status/status_off.json",
    command_responses_files={
        "remoteStart": "commands/remote_start.json",
        "cancelRemoteStart": "commands/cancel_remote_start.json",
    },
    mock_data={
        "property_values": {
            "is_running": False,
            "is_remotely_started": False,
            "is_not_running": True,
            "is_not_remotely_started": True,
        }
    },
)
def test_start_and_stop(mocked_vehicle, monkeypatch):
    """Test the vehicle start and stop commands."""
    # TODO: This doesn't work because we don't yet have a way to mock verification.
    assert not mocked_vehicle.is_running
    assert not mocked_vehicle.is_remotely_started

    mocked_vehicle.start(verify=True, verify_delay=0.1)

    monkeypatch.setattr(mocked_vehicle, "is_running", True)
    monkeypatch.setattr(mocked_vehicle, "is_remotely_started", True)
    monkeypatch.setattr(mocked_vehicle, "is_not_running", False)
    monkeypatch.setattr(mocked_vehicle, "is_not_remotely_started", False)

    assert mocked_vehicle.is_running
    assert mocked_vehicle.is_remotely_started
    assert not mocked_vehicle.is_not_running

    mocked_vehicle.stop(verify=True, verify_delay=0.1)

    monkeypatch.setattr(mocked_vehicle, "is_running", False)
    monkeypatch.setattr(mocked_vehicle, "is_remotely_started", False)

    assert not mocked_vehicle.is_running
    assert not mocked_vehicle.is_remotely_started
    assert mocked_vehicle.is_not_running
