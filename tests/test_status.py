"""Tests vehicle status using respx for mocking HTTP requests."""

import pytest
from respx import MockRouter

from vehiclepass import Vehicle
from vehiclepass.constants import AUTONOMIC_AUTH_URL, AUTONOMIC_TELEMETRY_BASE_URL
from vehiclepass.units import Distance, Temperature

from .conftest import mock_responses


@mock_responses(status="status/baseline.json")
def test_properties(vehicle: Vehicle):
    """Test baseline properties."""
    # Temperatures
    assert vehicle.outside_temp.c == 0.0
    assert vehicle.outside_temp.f == 32.0
    assert str(vehicle.outside_temp) == "32.0°F"
    assert vehicle.engine_coolant_temp.c == 89.0
    assert vehicle.engine_coolant_temp.f == 192.2
    assert str(vehicle.engine_coolant_temp) == "192.2°F"

    # Odometer
    assert vehicle.odometer.km == 105547.0
    assert vehicle.odometer.mi == 65583.84
    assert str(vehicle.odometer) == "65583.84 mi"

    # Tire pressure
    assert vehicle.tire_pressure.front_left.psi == 39.45
    assert str(vehicle.tire_pressure.front_left) == "39.45 psi"
    assert vehicle.tire_pressure.front_left.kpa == 272.0
    assert vehicle.tire_pressure.front_right.psi == 40.18
    assert str(vehicle.tire_pressure.front_right) == "40.18 psi"
    assert vehicle.tire_pressure.front_right.kpa == 277.0
    assert vehicle.tire_pressure.rear_left.psi == 39.89
    assert str(vehicle.tire_pressure.rear_left) == "39.89 psi"
    assert vehicle.tire_pressure.rear_left.kpa == 275.0
    assert vehicle.tire_pressure.rear_right.psi == 39.89
    assert str(vehicle.tire_pressure.rear_right) == "39.89 psi"
    assert vehicle.tire_pressure.rear_right.kpa == 275.0

    # Fuel
    assert vehicle.fuel_level.percentage == 0.72717624
    assert vehicle.fuel_level.percent == 0.73
    assert str(vehicle.fuel_level) == "73.0%"

    assert isinstance(vehicle.outside_temp, Temperature)
    assert isinstance(vehicle.odometer, Distance)


@mock_responses(status="status/remotely_started.json")
def test_status_remotely_started(vehicle: Vehicle):
    """Test status when vehicle is remotely started."""
    assert vehicle.is_running is True
    assert vehicle.is_remotely_started is True
    assert vehicle.shutoff_countdown.seconds == 851.0
    assert vehicle.shutoff_countdown.human_readable == "14m 11s"
    assert vehicle.is_ignition_started is False
    assert vehicle.fuel_level.percent == 0.74


@pytest.mark.parametrize("temp_c, temp_f", [(0, 32), (20, 68), (37, 98.6), (-10, 14)])
def test_temperature_conversion(vehicle: Vehicle, mock_router: MockRouter, temp_c: float, temp_f: float):
    """Test that temperature conversions work correctly."""
    mock_router.post(AUTONOMIC_AUTH_URL).respond(
        json={"access_token": "mock-token-12345", "token_type": "Bearer", "expires_in": 3600}
    )

    mock_router.get(f"{AUTONOMIC_TELEMETRY_BASE_URL}/MOCK12345").respond(
        json={"metrics": {"outsideTemperature": {"value": float(temp_c)}}}
    )

    temp = vehicle.outside_temp
    assert temp.c == temp_c
    assert round(temp.f, 1) == temp_f

    mock_router.reset()
