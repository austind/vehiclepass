"""Engine data."""

import datetime
import logging
import time
from typing import TYPE_CHECKING

from vehiclepass.units import Temperature

if TYPE_CHECKING:
    from vehiclepass.vehicle import Vehicle

logger = logging.getLogger(__name__)


class Engine:
    """Engine data."""

    def __init__(self, vehicle: "Vehicle"):
        """Initialize the engine class."""
        self._vehicle = vehicle

    def start(
        self,
        check_shutoff_time: bool = False,
        extend_shutoff_time: bool = False,
        extend_shutoff_time_delay: float | int = 30.0,
        verify: bool = False,
        verify_delay: float | int = 30.0,
        force: bool = False,
    ) -> None:
        """Request remote start.

        Args:
            check_shutoff_time: Whether to check and log the vehicle shutoff time
            extend_shutoff_time: Whether to extend the vehicle shutoff time by 15 minutes
            extend_shutoff_time_delay: Delay in seconds to wait before requesting vehicle shutoff extension
            verify: Whether to verify all commands' success after issuing them
            verify_delay: Delay in seconds to wait before verifying the commands' success
            force: Whether to issue the command even if the vehicle is already running

        """
        self._send_command(
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
        if extend_shutoff_time:
            logger.info("Waiting %d seconds before requesting shutoff extension...", extend_shutoff_time_delay)
            time.sleep(extend_shutoff_time_delay)
            self.extend_shutoff_time(verify=verify, verify_delay=verify_delay, force=force)

        if check_shutoff_time:
            self.refresh_status()
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

    def stop(self, verify: bool = False, verify_delay: float | int = 30.0, force: bool = False) -> None:
        """Shut off the engine.

        Args:
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success
            force: Whether to issue the command even if the vehicle i already not running

        Returns:
            None
        """
        self._send_command(
            command="cancelRemoteStart",
            verify=verify,
            verify_delay=verify_delay,
            check_predicate=lambda: self.is_not_running,
            success_msg="Vehicle's engine is now stopped",
            fail_msg="Vehicle's engine failed to stop",
            force=force,
            not_issued_msg="Vehicle is already stopped, no command issued",
            forced_msg="Vehicle is already stopped but force flag enabled, issuing command anyway...",
        )

    def extend_shutoff_time(self, verify: bool = False, verify_delay: float | int = 30.0, force: bool = False) -> None:
        """Extend the vehicle shutoff time by 15 minutes.

        Args:
            verify: Whether to verify the command's success after issuing it
            verify_delay: Delay in seconds to wait before verifying the command's success
            force: Whether to issue the command even if the vehicle's shutoff time is already extended

        Returns:
            None
        """
        self._send_command(
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

    @property
    def is_running(self) -> bool:
        """Check if the vehicle is running."""
        return self._vehicle._get_metric_value("ignitionStatus", str) == "ON"

    @property
    def is_not_running(self) -> bool:
        """Check if the vehicle is not running."""
        return self._vehicle._get_metric_value("ignitionStatus", str) == "OFF"

    @property
    def shutoff_time_seconds(self) -> float:
        """Get the vehicle shutoff time in seconds since epoch."""
        return self._vehicle._get_metric_value("shutoffTime", float)

    @property
    def shutoff_time(self) -> datetime.datetime:
        """Get the vehicle shutoff time."""
        return datetime.datetime.fromtimestamp(self.shutoff_time_seconds)

    @property
    def coolant_temp(self) -> Temperature:
        """Get the engine coolant temperature."""
        temp = self._vehicle._get_metric_value("engineCoolantTemp", float)
        return Temperature.from_celsius(temp)

    @property
    def rpm(self) -> int:
        """Get the engine's current RPM."""
        return self._vehicle._get_metric_value("engineSpeed", int)
