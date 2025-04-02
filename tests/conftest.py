"""Fixtures for testing the vehiclepass library using respx."""

import functools
import json
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import pytest
import respx
from httpx import Response

from vehiclepass.constants import AUTONOMIC_AUTH_URL, AUTONOMIC_COMMAND_BASE_URL, AUTONOMIC_TELEMETRY_BASE_URL

T = TypeVar("T")


def pytest_configure(config):
    """Configure pytest."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")


"""Mock responses fixture for testing the vehiclepass library."""

from typing import TypeVar

T = TypeVar("T")


def load_mock_json(file_path: str | Path) -> dict[str, Any]:
    """Load mock data from a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dict containing the loaded JSON data
    """
    original_path = Path(file_path)

    # Check if it's a relative path and try to find it in mock_data directory
    if not original_path.is_absolute():
        if original_path.exists():
            final_path = original_path
        else:
            relative_path = Path("tests/mock_data") / original_path
            if relative_path.exists():
                final_path = relative_path
            else:
                raise FileNotFoundError(f"Mock data file not found: {original_path}")

    with open(final_path) as f:
        return json.load(f)


def mock_responses(
    status: str | Path | dict[str, Any] | None = None,
    commands: dict[str, str | Path | dict[str, Any]] | None = None,
    auth_token: str = "mock-token-12345",
):
    """Decorator to mock API responses for a test function.

    Args:
        status: Path to JSON file with status data, or a dictionary with inline status data
        commands: Dict mapping command names to response file paths or dictionaries
            e.g. {'remoteStart': 'path/to/start_response.json'}
        auth_token: Mock auth token to return from auth endpoint

    Usage:
        @mock_responses(
            status="status/vehicle_status.json",
            commands={
                'remoteStart': 'commands/remote_start_response.json',
                'cancelRemoteStart': {'status': 'success', 'requestId': 'abc123'}
            }
        )
        def test_remote_start(vehicle):
            # All API requests will be mocked
            assert vehicle.remote_start()["status"] == "success"
    """

    def decorator(test_func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            with respx.mock(assert_all_called=False) as mock:
                # Mock auth endpoint
                mock.post(AUTONOMIC_AUTH_URL).respond(
                    json={"access_token": auth_token, "token_type": "Bearer", "expires_in": 3600}
                )

                # Mock status endpoint
                status_data = {}
                if status is not None:
                    if isinstance(status, (str | Path)):
                        status_data = load_mock_json(status)
                    else:
                        status_data = status

                mock.get(re.compile(rf"{AUTONOMIC_TELEMETRY_BASE_URL}/*")).respond(json=status_data)

                # Mock command endpoints
                def command_handler(request):
                    command_type = request.json().get("type")
                    response_data = {"status": "unknown"}

                    if commands and command_type in commands:
                        cmd_response = commands[command_type]
                        if isinstance(cmd_response, (str | Path)):
                            response_data = load_mock_json(cmd_response)
                        else:
                            response_data = cmd_response

                    return Response(200, json=response_data)

                mock.post(re.compile(rf"{AUTONOMIC_COMMAND_BASE_URL}/*")).side_effect = command_handler

                # Run the test
                return test_func(*args, **kwargs)

        return wrapper

    return decorator


@pytest.fixture
def vehicle():
    """Fixture for a basic Vehicle instance."""
    from vehiclepass import Vehicle

    return Vehicle(username="mock_user", password="mock_pass", vin="MOCK12345")


@pytest.fixture
def mock_router(request):
    """Create and configure a respx router for mocking HTTP requests."""
    with respx.mock(assert_all_called=False) as router:
        yield router
