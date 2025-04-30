"""Tests vehicle status using respx for mocking HTTP requests."""

import pytest
from pydantic_extra_types.coordinate import Coordinate, Latitude, Longitude
from respx import MockRouter

import vehiclepass
from tests.utils import mock_responses
from vehiclepass import units
from vehiclepass.constants import AUTONOMIC_AUTH_URL, AUTONOMIC_TELEMETRY_BASE_URL
from vehiclepass.seatbelts import SeatBelts
from vehiclepass.tires import Tires


@mock_responses(status="status/baseline.json")
def test_get_metric_value(vehicle: vehiclepass.Vehicle) -> None:
    """Test that _get_metric_value returns the correct value."""
    assert isinstance(vehicle._get_metric_value("batteryVoltage"), float)
    assert isinstance(vehicle._get_metric_value("compassDirection"), str)
    with pytest.raises(vehiclepass.StatusError):
        vehicle._get_metric_value("batteryVoltage", str)  # Incorrect type
        vehicle._get_metric_value("invalid_metric")


@mock_responses(status="status/baseline.json")
def test_tire_pressure(vehicle: vehiclepass.Vehicle) -> None:
    """Test tire pressure properties."""
    assert isinstance(vehicle.tires, Tires)
    assert isinstance(vehicle.tyres, Tires)

    # Front left
    assert getattr(vehicle.tires, "front_left").pressure.bar == 2.72
    assert getattr(vehicle.tires, "front_left").pressure.kpa == 272.0
    assert getattr(vehicle.tires, "front_left").pressure.psi == 39.45
    assert str(getattr(vehicle.tires, "front_left").pressure) == "39.45 psi"
    assert getattr(vehicle.tires, "front_left").pressure.data == {"psi": 39.45, "bar": 2.72, "kpa": 272.0}

    # Front right
    assert getattr(vehicle.tires, "front_right").pressure.bar == 2.77
    assert getattr(vehicle.tires, "front_right").pressure.kpa == 277.0
    assert getattr(vehicle.tires, "front_right").pressure.psi == 40.18
    assert str(getattr(vehicle.tires, "front_right").pressure) == "40.18 psi"
    assert getattr(vehicle.tires, "front_right").pressure.data == {"psi": 40.18, "bar": 2.77, "kpa": 277.0}

    # Rear left
    assert getattr(vehicle.tires, "rear_left").pressure.psi == 39.89
    assert getattr(vehicle.tires, "rear_left").pressure.bar == 2.75
    assert getattr(vehicle.tires, "rear_left").pressure.kpa == 275.0
    assert str(getattr(vehicle.tires, "rear_left").pressure) == "39.89 psi"
    assert getattr(vehicle.tires, "rear_left").pressure.data == {"psi": 39.89, "bar": 2.75, "kpa": 275.0}

    # Rear right
    assert getattr(vehicle.tires, "rear_right").pressure.bar == 2.75
    assert getattr(vehicle.tires, "rear_right").pressure.kpa == 275.0
    assert getattr(vehicle.tires, "rear_right").pressure.psi == 39.89
    assert getattr(vehicle.tires, "rear_right").pressure.data == {"psi": 39.89, "bar": 2.75, "kpa": 275.0}
    assert str(getattr(vehicle.tires, "rear_right").pressure) == "39.89 psi"


@mock_responses(status="status/baseline.json")
def test_tire_status(vehicle: vehiclepass.Vehicle) -> None:
    """Test tire status properties."""
    assert isinstance(vehicle.tires, Tires)
    assert getattr(vehicle.tires, "front_left").status == "NORMAL"
    assert getattr(vehicle.tires, "front_right").status == "NORMAL"
    assert getattr(vehicle.tires, "rear_left").status == "NORMAL"
    assert getattr(vehicle.tires, "rear_right").status == "NORMAL"


@mock_responses(status="status/baseline.json")
def test_seatbelts(vehicle: vehiclepass.Vehicle) -> None:
    """Test seatbelt status."""
    assert isinstance(vehicle.seatbelts, SeatBelts)
    assert getattr(vehicle.seatbelts, "driver") == "UNBUCKLED"
    assert getattr(vehicle.seatbelts, "passenger") == "UNBUCKLED"


@mock_responses(status="status/baseline.json")
def test_tires_system_status(vehicle: vehiclepass.Vehicle) -> None:
    """Test tire pressure system status."""
    assert vehicle.tires.system_status == "NORMAL_OPERATION"
    assert vehicle.tpms.system_status == "NORMAL_OPERATION"
    assert vehicle.tyres.system_status == "NORMAL_OPERATION"
    assert vehicle.tires.data == {
        "front_left": {"pressure": {"psi": 39.45, "bar": 2.72, "kpa": 272.0}, "status": "NORMAL"},
        "front_right": {"pressure": {"psi": 40.18, "bar": 2.77, "kpa": 277.0}, "status": "NORMAL"},
        "rear_left": {"pressure": {"psi": 39.89, "bar": 2.75, "kpa": 275.0}, "status": "NORMAL"},
        "rear_right": {"pressure": {"psi": 39.89, "bar": 2.75, "kpa": 275.0}, "status": "NORMAL"},
    }


@mock_responses(status="status/baseline.json")
def test_temperature(vehicle: vehiclepass.Vehicle) -> None:
    """Test temperature properties."""
    assert isinstance(vehicle.outside_temp, units.Temperature)
    assert vehicle.outside_temp.c == 0.0
    assert vehicle.outside_temp.f == 32.0
    assert str(vehicle.outside_temp) == "32.0°F"

    assert isinstance(vehicle.engine_coolant_temp, units.Temperature)
    assert vehicle.engine_coolant_temp.c == 89.0
    assert vehicle.engine_coolant_temp.f == 192.2
    assert str(vehicle.engine_coolant_temp) == "192.2°F"


@mock_responses(status="status/baseline.json")
def test_odometer(vehicle: vehiclepass.Vehicle) -> None:
    """Test odometer properties."""
    assert isinstance(vehicle.odometer, units.Distance)
    assert vehicle.odometer.km == 105547.0
    assert vehicle.odometer.mi == 65583.84
    assert str(vehicle.odometer) == "65583.84 mi"


@mock_responses(status="status/baseline.json")
def test_oil_life_remaining(vehicle: vehiclepass.Vehicle) -> None:
    """Test oil life remaining."""
    assert isinstance(vehicle.oil_life_remaining, units.Percentage)
    assert vehicle.oil_life_remaining.value == 0.51
    assert str(vehicle.oil_life_remaining) == "51.0%"


@mock_responses(status="status/baseline.json")
def test_fuel(vehicle: vehiclepass.Vehicle) -> None:
    """Test fuel properties."""
    assert isinstance(vehicle.fuel_level, units.Percentage)
    assert vehicle.fuel_level.value == 0.72717624
    assert vehicle.fuel_level.percent == 0.7272
    assert str(vehicle.fuel_level) == "72.72%"


@mock_responses(status="status/remotely_started.json")
def test_status_remotely_started(vehicle: vehiclepass.Vehicle) -> None:
    """Test status when vehicle is remotely started."""
    assert vehicle.is_running is True
    assert vehicle.is_remotely_started is True
    assert vehicle.shutoff_countdown.seconds == 851.0
    assert vehicle.shutoff_countdown.human_readable == "14m 11s"
    assert vehicle.is_ignition_started is False


@mock_responses(status="status/baseline.json")
def test_position(vehicle: vehiclepass.Vehicle) -> None:
    """Test vehicle position (GPS coordinates)."""
    assert isinstance(vehicle.position, Coordinate)
    assert vehicle.position.latitude == Latitude(42.31474)
    assert vehicle.position.longitude == Longitude(-83.21043)


@pytest.mark.parametrize("temp_c, temp_f", [(0, 32), (20, 68), (37, 98.6), (-10, 14)])
def test_temperature_conversion(vehicle: vehiclepass.Vehicle, mock_router: MockRouter, temp_c: float, temp_f: float):
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
