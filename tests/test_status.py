"""Tests vehicle status."""

import pytest

from vehiclepass.units import Distance, Temperature

from .conftest import with_vehicle_mock


def test_basic_properties(mocked_vehicle):
    """Test that basic vehicle properties work as expected."""
    assert mocked_vehicle.outside_temp is not None
    assert isinstance(mocked_vehicle.outside_temp, Temperature)
    assert isinstance(mocked_vehicle.odometer, Distance)
    assert mocked_vehicle.outside_temp.c == 22.0
    assert mocked_vehicle.is_running is True
    assert mocked_vehicle.is_remotely_started is True
    assert mocked_vehicle.shutoff_countdown.seconds == 903.0
    assert mocked_vehicle.shutoff_countdown.human_readable == "15m 3s"
    assert mocked_vehicle.is_ignition_started is False


@with_vehicle_mock(status_file="status/status_off.json")
def test_metrics_from_file(mocked_vehicle):
    """Test that vehicle metrics are correctly loaded from the status file."""
    # Temperatures
    assert mocked_vehicle.outside_temp.c == 0.0
    assert mocked_vehicle.outside_temp.f == 32.0
    assert mocked_vehicle.engine_coolant_temp.c == 89.0
    assert mocked_vehicle.engine_coolant_temp.f == 192.2

    # Odometer
    assert mocked_vehicle.odometer.km == 105547.0
    assert mocked_vehicle.odometer.mi == 65583.84

    # Tire pressure
    assert mocked_vehicle.tire_pressure.front_left.psi == 39.45
    assert str(mocked_vehicle.tire_pressure.front_left) == "39.45 psi"
    assert mocked_vehicle.tire_pressure.front_left.kpa == 272.0
    assert mocked_vehicle.tire_pressure.front_right.psi == 40.18
    assert str(mocked_vehicle.tire_pressure.front_right) == "40.18 psi"
    assert mocked_vehicle.tire_pressure.front_right.kpa == 277.0
    assert mocked_vehicle.tire_pressure.rear_left.psi == 39.89
    assert str(mocked_vehicle.tire_pressure.rear_left) == "39.89 psi"
    assert mocked_vehicle.tire_pressure.rear_left.kpa == 275.0
    assert mocked_vehicle.tire_pressure.rear_right.psi == 39.89
    assert str(mocked_vehicle.tire_pressure.rear_right) == "39.89 psi"
    assert mocked_vehicle.tire_pressure.rear_right.kpa == 275.0

    # Fuel
    assert mocked_vehicle.fuel_level.percent == 0.72717624
    assert str(mocked_vehicle.fuel_level) == "72.72%"


@with_vehicle_mock(
    status_file="status/status_off.json",
    metric_overrides={"outsideTemperature": 30.0, "engineCoolantTemp": 95.0},
)
def test_metric_overrides(mocked_vehicle):
    """Test that metric overrides work correctly."""
    # These should use our override values
    assert mocked_vehicle.outside_temp.c == 30.0
    assert mocked_vehicle.engine_coolant_temp.c == 95.0

    # Other metrics should still come from the file
    assert mocked_vehicle.odometer.km == 105547.0


@with_vehicle_mock(mock_data={"property_values": {"is_running": True, "is_remotely_started": True}})
def test_property_values(mocked_vehicle):
    """Test that property values can be directly set."""
    assert mocked_vehicle.is_running is True
    assert mocked_vehicle.is_remotely_started is True


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
def test_missing_metric(mocked_vehicle):
    """Test that appropriate errors are raised for missing metrics."""
    from vehiclepass.errors import StatusError

    with pytest.raises(StatusError):
        _ = mocked_vehicle.outside_temp


@pytest.mark.parametrize("temp_c,temp_f", [(0, 32), (20, 68), (37, 98.6), (-10, 14)])
def test_temperature_conversion(mocked_vehicle, temp_c, temp_f, monkeypatch):
    """Test that temperature conversions work correctly."""
    # Monkeypatch the _get_metric_value method to return our test value
    monkeypatch.setattr(
        mocked_vehicle,
        "_get_metric_value",
        lambda metric_name, expected_type=float: temp_c if metric_name == "outsideTemperature" else 0,
    )

    # Get the temperature and check conversions
    temp = mocked_vehicle.outside_temp
    assert temp.c == temp_c
    assert round(temp.f, 1) == temp_f


@with_vehicle_mock(status_file="status/status_off.json")
def test_specific_metrics(mocked_vehicle):
    """Test that specific metrics are correctly loaded from the status file."""
    assert mocked_vehicle.fuel_level.percent == 0.72717624
    assert mocked_vehicle.shutoff_countdown.seconds == 0.0
    assert f"{mocked_vehicle.outside_temp}" == "32.0°F"
    assert f"{mocked_vehicle.odometer}" == "65583.84 mi"
