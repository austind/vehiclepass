"""Constants."""

import os

from dotenv import load_dotenv

load_dotenv()

LOGIN_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"  # noqa: E501
FORDPASS_API_VERSION = "v1"  # v1beta is also valid, but differences are untested

# Don't change these.
FORDPASS_AUTH_URL = "https://us-central1-ford-connected-car.cloudfunctions.net/api/auth"
AUTONOMIC_AUTH_URL = "https://accounts.autonomic.ai/v1/auth/oidc/token"
AUTONOMIC_TELEMETRY_BASE_URL = f"https://api.autonomic.ai/{FORDPASS_API_VERSION}/telemetry/sources/fordpass/vehicles"
AUTONOMIC_COMMAND_BASE_URL = f"https://api.autonomic.ai/{FORDPASS_API_VERSION}/command/vehicles"
FORDPASS_APPLICATION_ID = "71A3AD0A-CF46-4CCF-B473-FC7FE5BC4592"
FORDPASS_CLIENT_ID = "9fb503e0-715b-47e8-adfd-ad4b7770f73b"
FORDPASS_USER_AGENT = "FordPass/2 CFNetwork/1475 Darwin/23.0.0"

# Used when rounding floats.
DECIMAL_PLACES = int(os.getenv("FORDPASS_DECIMAL_PLACES", "2"))

# Used when converting units to strings.
DEFAULT_TEMP_UNIT = os.getenv("VEHICLEPASS_DEFAULT_TEMP_UNIT", "f")
if DEFAULT_TEMP_UNIT not in ["f", "c"]:
    raise ValueError(f"VEHICLEPASS_DEFAULT_TEMP_UNIT: Invalid unit: {DEFAULT_TEMP_UNIT}. Valid units are: f, c")

DEFAULT_DISTANCE_UNIT = os.getenv("VEHICLEPASS_DEFAULT_DISTANCE_UNIT", "mi")
if DEFAULT_DISTANCE_UNIT not in ["mi", "km"]:
    raise ValueError(
        f"VEHICLEPASS_DEFAULT_DISTANCE_UNIT: Invalid unit: {DEFAULT_DISTANCE_UNIT}. Valid units are: mi, km"
    )

DEFAULT_PRESSURE_UNIT = os.getenv("VEHICLEPASS_DEFAULT_PRESSURE_UNIT", "psi")
if DEFAULT_PRESSURE_UNIT not in ["psi", "kpa"]:
    raise ValueError(
        f"VEHICLEPASS_DEFAULT_PRESSURE_UNIT: Invalid unit: {DEFAULT_PRESSURE_UNIT}. Valid units are: psi, kpa"
    )

DEFAULT_ELECTRIC_POTENTIAL_UNIT = os.getenv("VEHICLEPASS_DEFAULT_ELECTRIC_POTENTIAL_UNIT", "v")
if DEFAULT_ELECTRIC_POTENTIAL_UNIT not in ["v", "mv"]:
    raise ValueError(
        f"VEHICLEPASS_DEFAULT_ELECTRIC_POTENTIAL_UNIT: Invalid unit: {DEFAULT_ELECTRIC_POTENTIAL_UNIT}. "
        "Valid units are: v, mv"
    )

DEFAULT_TIME_UNIT = os.getenv("VEHICLEPASS_DEFAULT_TIME_UNIT", "s")
if DEFAULT_TIME_UNIT not in ["s", "m", "h", "ms", "human_readable"]:
    raise ValueError(
        f"VEHICLEPASS_DEFAULT_TIME_UNIT: Invalid unit: {DEFAULT_TIME_UNIT}. "
        "Valid units are: s, m, h, ms, human_readable"
    )
