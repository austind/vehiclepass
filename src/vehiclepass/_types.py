from typing import Literal

HoodStatus = Literal["OPEN", "CLOSED"]
CompassDirection = Literal["NORTH", "NORTHEAST", "EAST", "SOUTHEAST", "SOUTH", "SOUTHWEST", "WEST", "NORTHWEST"]
VehicleCommand = Literal["remoteStart", "cancelRemoteStart", "lock", "unlock"]
AlarmStatus = Literal["ARMED", "DISARMED"]
GearLeverPosition = Literal["PARK", "REVERSE", "NEUTRAL", "DRIVE", "MANUAL"]
