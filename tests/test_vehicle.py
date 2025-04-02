"""Tests for the Vehicle class."""

import pytest

from vehiclepass.units import Distance, Temperature

from .conftest import with_vehicle_mock

# # Optional setup function to create example mock files if they don't exist yet
# def setup_module(module):
#     """Create example mock files before running tests."""
#     try:
#         create_example_mock_files()
#     except Exception as e:
#         print(f"Warning: Could not create example mock files: {e}")


def test_vehicle_basic_properties(mocked_vehicle, vehicle_mock_data):
    """Test that basic vehicle properties work as expected."""
    assert mocked_vehicle.outside_temp is not None
    assert isinstance(mocked_vehicle.outside_temp, Temperature)
    assert isinstance(mocked_vehicle.odometer, Distance)
    assert mocked_vehicle.outside_temp.c == 22.0
    assert mocked_vehicle.is_running is True


@with_vehicle_mock(status_file="status/status_off.json")
def test_vehicle_metrics_from_file(mocked_vehicle):
    """Test that vehicle metrics are correctly loaded from the status file."""
    assert mocked_vehicle.outside_temp.c == 0.0
    assert mocked_vehicle.engine_coolant_temp.c == 89.0
    assert mocked_vehicle.odometer.km == 105547.0


@with_vehicle_mock(
    status_file="status/status_off.json",
    metric_overrides={"outsideTemperature": 30.0, "engineCoolantTemp": 95.0},
)
def test_vehicle_metric_overrides(mocked_vehicle):
    """Test that metric overrides work correctly."""
    # These should use our override values
    assert mocked_vehicle.outside_temp.c == 30.0
    assert mocked_vehicle.engine_coolant_temp.c == 95.0

    # Other metrics should still come from the file
    assert mocked_vehicle.odometer.km == 105547.0


@with_vehicle_mock(mock_data={"property_values": {"is_running": True, "is_remotely_started": True}})
def test_vehicle_property_values(mocked_vehicle):
    """Test that property values can be directly set."""
    assert mocked_vehicle.is_running is True
    assert mocked_vehicle.is_remotely_started is True


# Test using command-specific response files
@with_vehicle_mock(
    status_file="status/status_off.json",
    command_responses_files={
        "remoteStart": "commands/remote_start.json",
        "cancelRemoteStart": "commands/cancel_remote_start.json",
    },
    mock_data={"property_values": {"is_running": False, "is_remotely_started": False}},
)
def test_vehicle_command_responses(mocked_vehicle, monkeypatch):
    """Test that command responses are correctly loaded from files."""

    # Mock the check_predicate to always return True for simplicity
    def mock_true():
        return True

    # For start command, mock is_remotely_started to return False (off) then True (on) after command
    running_state = [False]  # Use a list so we can modify it inside the nested function

    def mock_remotely_started():
        return running_state[0]

    delattr(mocked_vehicle, "is_remotely_started")
    monkeypatch.setattr(mocked_vehicle, "is_remotely_started", mock_remotely_started)

    # Intercept the _send_command to check the response and update our state
    original_send_command = mocked_vehicle._send_command

    def mock_send_command(command, **kwargs):
        response = original_send_command(command, **kwargs)
        if command == "remoteStart":
            running_state[0] = True
        elif command == "cancelRemoteStart":
            running_state[0] = False
        return response

    monkeypatch.setattr(mocked_vehicle, "_send_command", mock_send_command)

    # Initially the vehicle should not be running
    assert not mocked_vehicle.is_remotely_started

    # Start the vehicle with our mocked check_predicate
    response = mocked_vehicle._send_command("remoteStart", check_predicate=mock_true, verify=False)

    # The response should come from the remote_start_response.json file
    assert response["status"] == "success"
    assert "requestId" in response

    # Our state should be updated to running
    assert mocked_vehicle.is_remotely_started

    # Now stop the vehicle
    response = mocked_vehicle._send_command("cancelRemoteStart", check_predicate=mock_true, verify=False)

    # The response should come from the cancel_remote_start_response.json file
    assert response["status"] == "success"
    assert "requestId" in response

    # Our state should be updated to not running
    assert not mocked_vehicle.is_remotely_started


# Test start and stop methods with command-specific response files
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
def test_vehicle_start_stop_methods(mocked_vehicle, monkeypatch):
    """Test the vehicle start and stop methods with command-specific response files."""
    # Initially the vehicle should not be running
    assert not mocked_vehicle.is_running
    assert not mocked_vehicle.is_remotely_started

    # For mocking state changes
    running_states = {
        "is_running": False,
        "is_remotely_started": False,
        "is_not_running": True,
        "is_not_remotely_started": True,
    }

    def get_property_mock(prop_name):
        return lambda self: running_states[prop_name]

    # Set up the property mocks
    for prop_name in running_states:
        monkeypatch.setattr(type(mocked_vehicle), prop_name, property(get_property_mock(prop_name)))

    # Intercept _send_command to update our state
    original_send_command = mocked_vehicle._send_command

    def mock_send_command(command, **kwargs):
        response = original_send_command(command, **kwargs)

        # Update our state based on the command
        if command == "remoteStart":
            running_states["is_running"] = True
            running_states["is_remotely_started"] = True
            running_states["is_not_running"] = False
            running_states["is_not_remotely_started"] = False

        elif command == "cancelRemoteStart":
            running_states["is_running"] = False
            running_states["is_remotely_started"] = False
            running_states["is_not_running"] = True
            running_states["is_not_remotely_started"] = True

        # If this is a check_predicate call, make it return the right thing
        if "check_predicate" in kwargs and kwargs["check_predicate"] is not None:
            # Temporarily monkeypatch the check_predicate to return the expected value
            if command == "remoteStart":
                monkeypatch.setattr(
                    kwargs["check_predicate"], "__call__", lambda: running_states["is_remotely_started"]
                )
            elif command == "cancelRemoteStart":
                monkeypatch.setattr(kwargs["check_predicate"], "__call__", lambda: running_states["is_not_running"])

        return response

    monkeypatch.setattr(mocked_vehicle, "_send_command", mock_send_command)

    # Now test the start method - this should call _send_command with remoteStart
    mocked_vehicle.start(verify=True, verify_delay=0.1)

    # Vehicle should now be running
    assert mocked_vehicle.is_running
    assert mocked_vehicle.is_remotely_started
    assert not mocked_vehicle.is_not_running

    # Now test the stop method - this should call _send_command with cancelRemoteStart
    mocked_vehicle.stop(verify=True, verify_delay=0.1)

    # Vehicle should now be stopped
    assert not mocked_vehicle.is_running
    assert not mocked_vehicle.is_remotely_started
    assert mocked_vehicle.is_not_running


# Test multiple command responses in sequence
@with_vehicle_mock(
    status_file="status/status_off.json",
    command_responses_files={
        "remoteStart": "commands/remote_start.json",
        "cancelRemoteStart": "commands/cancel_remote_start.json",
        "lock": "commands/lock.json",
        "unlock": "commands/unlock.json",
    },
    mock_data={"property_values": {"is_running": False, "is_remotely_started": False}},
)
def test_multiple_commands(mocked_vehicle, monkeypatch):
    """Test a sequence of different commands with different response files."""

    # Mock the check_predicate to always return True for simplicity
    def mock_true():
        return True

    # Keep track of which commands were called
    command_sequence = []

    # Intercept the _send_command to record the sequence
    original_send_command = mocked_vehicle._send_command

    def mock_send_command(command, **kwargs):
        command_sequence.append(command)
        return original_send_command(command, **kwargs)

    monkeypatch.setattr(mocked_vehicle, "_send_command", mock_send_command)

    # Test a series of commands
    unlock_response = mocked_vehicle._send_command("unlock", check_predicate=mock_true)
    assert unlock_response["currentStatus"] == "REQUESTED"

    start_response = mocked_vehicle._send_command("remoteStart", check_predicate=mock_true)
    assert start_response["currentStatus"] == "REQUESTED"

    lock_response = mocked_vehicle._send_command("lock", check_predicate=mock_true)
    assert lock_response["currentStatus"] == "REQUESTED"

    stop_response = mocked_vehicle._send_command("cancelRemoteStart", check_predicate=mock_true)
    assert stop_response["currentStatus"] == "REQUESTED"

    # Verify the command sequence
    assert command_sequence == ["unlock", "remoteStart", "lock", "cancelRemoteStart"]

    # Each response should have a different requestId from their respective files
    assert unlock_response["requestId"] != start_response["requestId"]
    assert start_response["requestId"] != lock_response["requestId"]
    assert lock_response["requestId"] != stop_response["requestId"]


# Test for error cases
@with_vehicle_mock(
    status_file="status/status_off.json",
    mock_data={
        "status": {
            "metrics": {
                # This will override the status file for this metric
                "outsideTemperature": None
            }
        }
    },
)
def test_vehicle_missing_metric(mocked_vehicle):
    """Test that appropriate errors are raised for missing metrics."""
    from vehiclepass.errors import VehiclePassStatusError

    # This should raise an error since we set the metric to None
    with pytest.raises(VehiclePassStatusError):
        _ = mocked_vehicle.outside_temp


# Parametrized test for different temperature values
@pytest.mark.parametrize("temp_c,temp_f", [(0, 32), (20, 68), (37, 98.6), (-10, 14)])
def test_vehicle_temperature_conversion(mocked_vehicle, temp_c, temp_f, monkeypatch):
    """Test that temperature conversions work correctly."""
    # Monkeypatch the _get_metric_value method to return our test value
    monkeypatch.setattr(
        mocked_vehicle,
        "_get_metric_value",
        lambda self, metric_name, expected_type=None: temp_c if metric_name == "outsideTemperature" else 0,
    )

    # Get the temperature and check conversions
    temp = mocked_vehicle.outside_temp
    assert temp.c == temp_c
    assert round(temp.f, 1) == temp_f


# Test to verify loading specific metrics from status file
@with_vehicle_mock(status_file="status/status_off.json")
def test_vehicle_specific_metrics(mocked_vehicle):
    """Test that specific metrics are correctly loaded from the status file."""
    assert mocked_vehicle.fuel_level == 0.72717624
    assert mocked_vehicle.shutoff_seconds == 0.0
    assert f"{mocked_vehicle.outside_temp}" == "0.0°C"
    assert f"{mocked_vehicle.odometer}" == "105547.0 km"
