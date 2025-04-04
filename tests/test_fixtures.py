"""Test fixtures."""

import vehiclepass

from .conftest import mock_responses


@mock_responses(
    status=[
        "status/baseline.json",
        "status/remotely_started.json",
        "status/remotely_started_extended.json",
        "status/baseline.json",
    ]
)
def test_mock_status_responses(vehicle: vehiclepass.Vehicle):
    """Test that mock responses are correctly loaded in order."""
    vehicle.refresh_status()  # Baseline
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.is_not_ignition_started
    assert vehicle._remote_start_count == 0

    vehicle.refresh_status()  # Remotely started
    assert vehicle.is_running
    assert vehicle.is_remotely_started
    assert vehicle.shutoff_countdown.seconds == 851.0

    vehicle.refresh_status()  # Remote started extended
    assert vehicle.shutoff_countdown.seconds == 1719.0

    vehicle.refresh_status()  # Baseline
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.shutoff_countdown.seconds == 0.0

    # Provided status responses are exhausted, so the last response is repeated.
    vehicle.refresh_status()
    assert vehicle.is_not_running
    assert vehicle.is_not_remotely_started
    assert vehicle.shutoff_countdown.seconds == 0.0
