"""Fixtures for testing the vehiclepass library using respx."""

import functools
import json
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import httpx
import pytest
import respx

from vehiclepass.constants import AUTONOMIC_AUTH_URL, AUTONOMIC_COMMAND_BASE_URL, AUTONOMIC_TELEMETRY_BASE_URL

T = TypeVar("T")


def pytest_configure(config):
    """Configure pytest."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")


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
    status: str | Path | list[str | Path] | dict[str, Any] | None = None,
    commands: dict[str, str | Path | list[str | Path] | dict[str, Any]] | None = None,
    auth_token: str = "mock-token-12345",
):
    """Decorator to mock API responses for a test function.

    Args:
        status: Path to JSON file with status data, or a dictionary with inline status data,
               or a list of paths/dicts to return sequentially
        commands: Dict mapping command names to response file paths, dictionaries,
                 or lists of paths/dicts to return sequentially
                 e.g. {'remoteStart': 'path/to/start_response.json'} or
                      {'remoteStart': ['response1.json', 'response2.json']}
        auth_token: Mock auth token to return from auth endpoint
    Usage:
        @mock_responses(
            status="status/vehicle_status.json",
            commands={
                'remoteStart': 'commands/remote_start_response.json',
                'cancelRemoteStart': {'status': 'success', 'requestId': 'abc123'},
                'sequentialCommand': ['response1.json', 'response2.json', {'status': 'complete'}]
            }
        )
        def test_remote_start(vehicle):
            # All API requests will be mocked
            assert vehicle.remote_start()["status"] == "success"
    """

    def decorator(test_func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to mock API responses for a test function.

        Args:
            test_func: The test function to decorate
        Returns:
            The decorated test function
        """

        def get_response_data(source):
            if isinstance(source, (str | Path)):
                return load_mock_json(source)
            return source

        def status_handler(
            status: str | Path | list[str | Path] | dict[str, Any] | None,
        ) -> list[httpx.Response]:
            if status is None:
                return []
            if isinstance(status, (str | Path)):
                return [httpx.Response(status_code=200, json=load_mock_json(status))]
            if isinstance(status, list):
                return [
                    httpx.Response(
                        status_code=200,
                        json=load_mock_json(status_file) if isinstance(status_file, (str | Path)) else status_file,
                    )
                    for status_file in status
                ]
            return [httpx.Response(status_code=200, json=status)]

        # Track command call counts for iterables
        command_counters = dict.fromkeys(commands, 0) if commands else {}

        def command_handler(request):
            # Extract command type from request
            try:
                request_body = request.content.decode("utf-8")
                command_type = json.loads(request_body).get("type")
            except (json.JSONDecodeError, AttributeError):
                return httpx.Response(200, json={"status": "unknown"})

            # Return default response if command not found
            if not commands or command_type not in commands:
                return httpx.Response(200, json={"status": "unknown"})

            # Get the command response (file path, dict, or list)
            cmd_response = commands[command_type]

            # Handle list of responses (sequential)
            if isinstance(cmd_response, list):
                idx = command_counters[command_type]
                # If we've gone through all responses, use the last one
                if idx >= len(cmd_response):
                    idx = len(cmd_response) - 1
                else:
                    command_counters[command_type] += 1

                response_data = get_response_data(cmd_response[idx])
            # Handle single response
            else:
                response_data = get_response_data(cmd_response)

            return httpx.Response(200, json=response_data)

        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            with respx.mock(assert_all_called=False) as mock:
                # Mock auth endpoint
                mock.post(AUTONOMIC_AUTH_URL).respond(
                    json={"access_token": auth_token, "token_type": "Bearer", "expires_in": 3600}
                )

                # Mock status endpoint
                side_effects = status_handler(status)
                mock.get(re.compile(rf"{AUTONOMIC_TELEMETRY_BASE_URL}/*")).side_effect = side_effects

                # Mock command endpoints with iterables support
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
