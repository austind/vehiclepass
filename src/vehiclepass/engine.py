"""Engine data."""

import datetime
import logging
import time
from typing import TYPE_CHECKING

from vehiclepass.errors import VehiclePassStatusError
from vehiclepass.units import Temperature

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle

logger = logging.getLogger(__name__)


class Engine:
    """Engine data."""

    def __init__(self, vehicle: "Vehicle"):
        """Initialize the engine class."""
        self._vehicle = vehicle
        self._remote_start_count = 0

    @property
    def remote_start_status(self) -> dict:
        """Get the remote start status."""
        try:
            return self._vehicle.status["events"]["remoteStartEvent"]
        except KeyError:
            raise VehiclePassStatusError("Unable to determine remote start status.")

    def start(
        self,
        extend_shutoff: bool = False,
        extend_shutoff_delay: float | int = 30.0,
        verify: bool = True,
        verify_delay: float | int = 30.0,
        force: bool = False,
    ) -> None:
        """Request remote start.

        Args:
            extend_shutoff: Whether to extend the vehicle shutoff time by 15 minutes
            extend_shutoff_delay: Delay in seconds to wait before requesting vehicle shutoff extension
            verify: Whether to verify all commands' success after issuing them
            verify_delay: Delay in seconds to wait before verifying the commands' success
            force: Whether to issue the command even if the vehicle is already running

        """
        self._vehicle._send_command(
            command="remoteStart",
            verify=verify,
            verify_delay=verify_delay,
            check_predicate=lambda: self.is_running,
            success_msg="Vehicle is now running",
            fail_msg="Vehicle failed to start",
            force=force,
            not_issued_msg="Vehicle is not running, no command issued",
            forced_msg="Vehicle is already running but force flag enabled, issuing command anyway...",
        )
        self._remote_start_count += 1
        if extend_shutoff:
            self.extend_shutoff(verify=verify, verify_delay=verify_delay, force=force, delay=extend_shutoff_delay)

        if verify:
            seconds = self.shutoff_time_seconds
            if seconds is not None:
                shutoff = self.shutoff_time
                logger.info(
                    "Vehicle will shut off at %s local time (in %.0f seconds)",
                    shutoff.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                    seconds,
                )
            else:
                logger.warning("Unable to determine vehicle shutoff time")

    def stop(self, verify: bool = True, verify_delay: float | int = 30.0, force: bool = False) -> None:
        """Shut off the engine.

        Args:
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success
            force: Whether to issue the command even if the vehicle is already shut off

        Returns:
            None
        """
        self._vehicle._send_command(
            command="cancelRemoteStart",
            verify=verify,
            verify_delay=verify_delay,
            check_predicate=lambda: self.is_not_running,
            force=force,
            success_msg="Vehicle's engine is now stopped",
            fail_msg="Vehicle's engine failed to stop",
            not_issued_msg="Vehicle is already stopped, no command issued",
            forced_msg="Vehicle is already stopped but force flag enabled, issuing command anyway...",
        )

    def extend_shutoff(
        self, verify: bool = False, verify_delay: float | int = 30.0, force: bool = False, delay: float | int = 30.0
    ) -> None:
        """Extend the vehicle shutoff time by 15 minutes.

        Args:
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success
            force: Whether to issue the command even if the vehicle's shutoff time is already extended
            delay: Delay in seconds to wait before issuing the command
        Returns:
            None
        """
        if not self.is_running:
            if force:
                logger.info(
                    "Vehicle is not running, but force flag enabled, issuing shutoff extension command anyway..."
                )
            else:
                logger.info("Vehicle is not running, shutoff extension command not issued.")
                return

        if self._remote_start_count >= 2:
            if force:
                logger.info(
                    "Vehicle has already been issued the maximum 2 remote start requests, "
                    "but force flag enabled, issuing shutoff extension command anyway..."
                )
            else:
                logger.info(
                    "Vehicle has already been issued the maximum 2 remote start requests, "
                    "shutoff extension command not issued."
                )
                return

        if delay:
            logger.info("Waiting %d seconds before requesting shutoff extension...", delay)
            time.sleep(delay)

        self._vehicle._send_command(
            command="remoteStart",
            verify=verify,
            verify_delay=verify_delay,
            check_predicate=lambda: self.is_running,  # TODO: Make correct predicate property
            success_msg="Shutoff time extended successfully",
            fail_msg="Shutoff time extension failed",
            force=force,
            not_issued_msg="Vehicle is not running, no command issued",
            forced_msg="Vehicle is already running but force flag enabled, issuing command anyway...",
        )
        self._remote_start_count += 1

    @property
    def is_running(self) -> bool:
        """Check if the vehicle is running, from either the ignition or a remote start command."""
        return self._vehicle._get_metric_value("ignitionStatus", str) == "ON" or self.is_remotely_started

    @property
    def is_not_running(self) -> bool:
        """Check if the vehicle is not running, from either the ignition or a remote start command."""
        return self._vehicle._get_metric_value("ignitionStatus", str) == "OFF" and not self.is_remotely_started

    @property
    def is_remotely_started(self) -> bool:
        """Check if the vehicle is running from a remote start command (but not from the ignition)."""
        try:
            return (
                "remoteStartBegan" in self.remote_start_status["conditions"]
                and self.remote_start_status["conditions"]["remoteStartBegan"]["remoteStartDeviceStatus"]["value"]
                == "RUNNING"
            )
        except KeyError as e:
            raise VehiclePassStatusError("Unable to determine if vehicle is remotely started.") from e

    @property
    def is_not_remotely_started(self) -> bool:
        """Check if the vehicle is not running from a remote start command (but not from the ignition)."""
        return not self.is_remotely_started

    @property
    def shutoff_countdown(self) -> float:
        """Get the vehicle shutoff time in seconds."""
        return self._vehicle._get_metric_value("remoteStartCountdownTimer", float)

    @property
    def shutoff_time(self) -> datetime.datetime | None:
        """Get the vehicle shutoff time."""
        if self.shutoff_countdown == 0.0:
            return None
        return datetime.datetime.now() + datetime.timedelta(seconds=self.shutoff_countdown)

    @property
    def coolant_temp(self) -> Temperature:
        """Get the engine coolant temperature."""
        temp = self._vehicle._get_metric_value("engineCoolantTemp", float)
        return Temperature.from_celsius(temp)

    @property
    def rpm(self) -> int:
        """Get the engine's current RPM."""
        return self._vehicle._get_metric_value("engineSpeed", int)
