"""Vehicle indicators class."""

from typing import TYPE_CHECKING, Any

from vehiclepass.errors import StatusError

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle


class Indicators:
    """Represents the vehicle indicator states."""

    def __init__(self, vehicle: "Vehicle") -> None:
        """Initialize the Indicators object.

        Args:
            vehicle: The parent vehicle object.
        """
        self._vehicle = vehicle
        self._indicators: dict[str, Any] = {}

    def _get_indicator_value(self, indicator_name: str) -> bool:
        """Get an indicator value with error handling.

        Args:
            indicator_name: The name of the indicator to retrieve

        Returns:
            bool: The indicator value

        Raises:
            StatusError: If the indicator is not found or its value is missing
        """
        if not self._indicators:
            self._indicators = self._vehicle._get_metric_value("indicators", dict)

        if indicator_name not in self._indicators:
            raise StatusError(f"{indicator_name} indicator status not found")

        indicator = self._indicators[indicator_name]
        if "value" not in indicator:
            raise StatusError(f"{indicator_name} indicator value is missing")

        return indicator["value"]

    @property
    def any_active(self) -> bool:
        """Check if any indicators are currently active.

        Returns:
            bool: True if any indicator is on, False if all indicators are off
        """
        return any(self._get_indicator_value(indicator) for indicator in self._indicators.keys())

    @property
    def active(self) -> list[str]:
        """Get a list of currently active indicators.

        Returns:
            list[str]: List of human-readable names of active indicators
        """
        active = []
        for name in self._indicators.keys():
            if self._get_indicator_value(name):
                active.append(name)
        return active

    @property
    def air_filter_minder(self) -> bool:
        """Check if air filter minder indicator is on."""
        return self._get_indicator_value("airFilterMinder")

    @property
    def adaptive_cruise_control(self) -> bool:
        """Check if adaptive cruise control indicator is on."""
        return self._get_indicator_value("adaptiveCruiseControl")

    @property
    def air_suspension_fault(self) -> bool:
        """Check if air suspension fault indicator is on."""
        return self._get_indicator_value("airSuspensionRideControlFault")

    @property
    def all_wheel_drive_disabled(self) -> bool:
        """Check if all wheel drive disabled indicator is on."""
        return self._get_indicator_value("allWheelDriveDisabled")

    @property
    def anti_theft(self) -> bool:
        """Check if anti-theft indicator is on."""
        return self._get_indicator_value("antiTheft")

    @property
    def antilock_brake(self) -> bool:
        """Check if antilock brake indicator is on."""
        return self._get_indicator_value("antilockBrake")

    @property
    def blind_spot_detection(self) -> bool:
        """Check if blind spot detection indicator is on."""
        return self._get_indicator_value("blindSpotDetection")

    @property
    def brake_warning(self) -> bool:
        """Check if brake warning indicator is on."""
        return self._get_indicator_value("brakeWarning")

    @property
    def charge_system_fault(self) -> bool:
        """Check if charge system fault indicator is on."""
        return self._get_indicator_value("chargeSystemFault")

    @property
    def check_fuel_cap(self) -> bool:
        """Check if check fuel cap indicator is on."""
        return self._get_indicator_value("checkFuelCap")

    @property
    def check_fuel_fill_inlet(self) -> bool:
        """Check if check fuel fill inlet indicator is on."""
        return self._get_indicator_value("checkFuelFillInlet")

    @property
    def diesel_engine_idle_shutdown(self) -> bool:
        """Check if diesel engine idle shutdown indicator is on."""
        return self._get_indicator_value("dieselEngineIdleShutdown")

    @property
    def diesel_engine_warning(self) -> bool:
        """Check if diesel engine warning indicator is on."""
        return self._get_indicator_value("dieselEngineWarning")

    @property
    def diesel_exhaust_fluid_low(self) -> bool:
        """Check if diesel exhaust fluid low indicator is on."""
        return self._get_indicator_value("dieselExhaustFluidLow")

    @property
    def diesel_exhaust_fluid_system_fault(self) -> bool:
        """Check if diesel exhaust fluid system fault indicator is on."""
        return self._get_indicator_value("dieselExhaustFluidSystemFault")

    @property
    def diesel_exhaust_over_temp(self) -> bool:
        """Check if diesel exhaust over temp indicator is on."""
        return self._get_indicator_value("dieselExhaustOverTemp")

    @property
    def diesel_particulate_filter(self) -> bool:
        """Check if diesel particulate filter indicator is on."""
        return self._get_indicator_value("dieselParticulateFilter")

    @property
    def diesel_pre_heat(self) -> bool:
        """Check if diesel pre heat indicator is on."""
        return self._get_indicator_value("dieselPreHeat")

    @property
    def electric_trailer_brake_connection(self) -> bool:
        """Check if electric trailer brake connection indicator is on."""
        return self._get_indicator_value("electricTrailerBrakeConnection")

    @property
    def engine_coolant_over_temp(self) -> bool:
        """Check if engine coolant over temp indicator is on."""
        return self._get_indicator_value("engineCoolantOverTemp")

    @property
    def fasten_seat_belt_warning(self) -> bool:
        """Check if fasten seat belt warning indicator is on."""
        return self._get_indicator_value("fastenSeatBeltWarning")

    @property
    def forward_collision_warning(self) -> bool:
        """Check if forward collision warning indicator is on."""
        return self._get_indicator_value("forwardCollisionWarning")

    @property
    def fuel_door_open(self) -> bool:
        """Check if fuel door open indicator is on."""
        return self._get_indicator_value("fuelDoorOpen")

    @property
    def hev_hazard(self) -> bool:
        """Check if HEV hazard indicator is on."""
        return self._get_indicator_value("hevHazard")

    @property
    def hill_descent_control_fault(self) -> bool:
        """Check if hill descent control fault indicator is on."""
        return self._get_indicator_value("hillDescentControlFault")

    @property
    def hill_start_assist_warning(self) -> bool:
        """Check if hill start assist warning indicator is on."""
        return self._get_indicator_value("hillStartAssistWarning")

    @property
    def lane_keeping_aid(self) -> bool:
        """Check if lane keeping aid indicator is on."""
        return self._get_indicator_value("laneKeepingAid")

    @property
    def lighting_system_failure(self) -> bool:
        """Check if lighting system failure indicator is on."""
        return self._get_indicator_value("lightingSystemFailure")

    @property
    def low_engine_oil_pressure(self) -> bool:
        """Check if low engine oil pressure indicator is on."""
        return self._get_indicator_value("lowEngineOilPressure")

    @property
    def low_fuel(self) -> bool:
        """Check if low fuel indicator is on."""
        return self._get_indicator_value("lowFuel")

    @property
    def low_washer_fluid(self) -> bool:
        """Check if low washer fluid indicator is on."""
        return self._get_indicator_value("lowWasherFluid")

    @property
    def malfunction_indicator(self) -> bool:
        """Check if malfunction indicator is on."""
        return self._get_indicator_value("malfunctionIndicator")

    @property
    def park_aid_malfunction(self) -> bool:
        """Check if park aid malfunction indicator is on."""
        return self._get_indicator_value("parkAidMalfunction")

    @property
    def passive_entry_passive_start(self) -> bool:
        """Check if passive entry passive start indicator is on."""
        return self._get_indicator_value("passiveEntryPassiveStart")

    @property
    def powertrain_malfunction(self) -> bool:
        """Check if powertrain malfunction indicator is on."""
        return self._get_indicator_value("powertrainMalfunction")

    @property
    def restraints_indicator_warning(self) -> bool:
        """Check if restraints indicator warning is on."""
        return self._get_indicator_value("restraintsIndicatorWarning")

    @property
    def service_steering(self) -> bool:
        """Check if service steering indicator is on."""
        return self._get_indicator_value("serviceSteering")

    @property
    def start_stop_engine_warning(self) -> bool:
        """Check if start stop engine warning indicator is on."""
        return self._get_indicator_value("startStopEngineWarning")

    @property
    def traction_control_disabled(self) -> bool:
        """Check if traction control disabled indicator is on."""
        return self._get_indicator_value("tractionControlDisabled")

    @property
    def traction_control_event(self) -> bool:
        """Check if traction control event indicator is on."""
        return self._get_indicator_value("tractionControlEvent")

    @property
    def tire_pressure_monitor_system_warning(self) -> bool:
        """Check if tire pressure monitor system warning indicator is on."""
        return self._get_indicator_value("tirePressureMonitorSystemWarning")

    @property
    def water_in_fuel(self) -> bool:
        """Check if water in fuel indicator is on."""
        return self._get_indicator_value("waterInFuel")

    def __repr__(self) -> str:
        """Return a string representation of the Indicators object."""
        return f"Indicators(active={self.active})"
