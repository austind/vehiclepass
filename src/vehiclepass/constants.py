"""Constants."""

LOGIN_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"  # noqa: E501
FORDPASS_USER_AGENT = "FordPass/2 CFNetwork/1475 Darwin/23.0.0"
FORDPASS_APPLICATION_ID = "71A3AD0A-CF46-4CCF-B473-FC7FE5BC4592"
FORDPASS_CLIENT_ID = "9fb503e0-715b-47e8-adfd-ad4b7770f73b"

FORDPASS_API_VERSION = "v1"
FORDPASS_AUTH_URL = "https://us-central1-ford-connected-car.cloudfunctions.net/api/auth"
AUTONOMIC_AUTH_URL = "https://accounts.autonomic.ai/v1/auth/oidc/token"
AUTONOMIC_TELEMETRY_BASE_URL = f"https://api.autonomic.ai/{FORDPASS_API_VERSION}/telemetry/sources/fordpass/vehicles"
AUTONOMIC_COMMAND_BASE_URL = (
    f"https://api.autonomic.ai/{FORDPASS_API_VERSION}/command/vehicles"
)

# Number of seconds to wait between commands.
# Recommended to be at least 5 seconds.
COMMAND_DELAY = 5
