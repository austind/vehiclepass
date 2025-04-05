"""Fixtures for testing the vehiclepass library using respx."""

import functools
import json
import logging
import re
from collections.abc import Callable, Iterable
from itertools import chain, repeat
from pathlib import Path
from typing import Any, TypeVar, Union

import httpx
import pytest
import respx

from vehiclepass.constants import (
    AUTONOMIC_AUTH_URL,
    AUTONOMIC_COMMAND_BASE_URL,
    AUTONOMIC_TELEMETRY_BASE_URL,
    FORDPASS_AUTH_URL,
)

T = TypeVar("T")

MOCK_RESPONSES_DIR = Path(__file__).parent / "fixtures" / "responses"


def pytest_configure(config):
    """Configure pytest."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")


def load_mock_json(file_path: Union[str, Path]) -> dict[str, Any]:
    """Load mock data from a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dict containing the loaded JSON data
    """
    original_path = Path(file_path)
    final_path = original_path

    # Check if it's a relative path and try to find it in mock_data directory
    if not original_path.is_absolute():
        if original_path.exists():
            final_path = original_path
        else:
            relative_path = MOCK_RESPONSES_DIR / original_path
            if relative_path.exists():
                final_path = relative_path
            else:
                raise FileNotFoundError(f"Mock data file not found: {original_path}")

    with open(final_path) as f:
        return json.load(f)


def mock_responses(
    status: Union[httpx.Response, str, Path, list[Union[str, Path, httpx.Response]], dict[str, Any], None] = None,
    commands: Union[
        dict[str, Union[httpx.Response, str, Path, list[Union[str, Path, httpx.Response]], dict[str, Any]]], None
    ] = None,
    auth_token: str = "mock-token-12345",
):
    """Test decorator that mocks HTTP API responses.

    Intercepts network requests for the FordPass API and returns predefined mock
    responses instead of making actual API calls.

    Args:
        status: Controls responses for status/telemetry endpoint requests.
            - httpx.Response: Used directly as the response
            - str or Path: Path to a JSON file, loaded and returned with 200 status code
            - dict: Raw JSON data, returned with 200 status code
            - list: Multiple responses returned in sequence for consecutive calls
              (last item repeats for any additional calls)
            - None: Returns a default baseline status from "status/baseline.json"

        commands: Controls responses for vehicle command endpoint requests.
            - dict mapping command names to response definitions
            - Each response can be a str/Path to JSON file, raw dict, or a list of
              responses returned in sequence (like status)
            - None: All command requests return 404

        auth_token: The mock authentication token to use for all authorized requests.

    Returns:
        A decorated test function that runs within the mocked HTTP environment.

    Example:
        @mock_responses(
            status="tests/mocks/vehicle_status.json",
            commands={
                "unlock": "tests/mocks/unlock_success.json",
                "lock": [
                    "tests/mocks/command_accepted.json",
                    "tests/mocks/lock_complete.json"
                ]
            }
        )
        def test_vehicle_commands(self):
            # Test code that makes API calls, which will now use mock responses
            ...
    """

    def decorator(test_func: Callable[..., T]) -> Callable[..., T]:
        def get_response_data(source):
            if isinstance(source, (str, Path)):
                return load_mock_json(source)
            return source

        command_indexes = {}

        def get_response(source_data, index_tracker):
            # For non-list sources, just return the data directly
            if not isinstance(source_data, list):
                return get_response_data(source_data)

            # For lists, return the current item or the last one if we've reached the end
            current = index_tracker["current"]
            if current < len(source_data) - 1:
                index_tracker["current"] = current + 1
                return get_response_data(source_data[current])
            # Return the last item for all subsequent calls
            return get_response_data(source_data[-1])

        def status_handler() -> Union[Iterable[httpx.Response], httpx.Response]:
            if isinstance(status, (str, Path)):
                return httpx.Response(status_code=200, json=load_mock_json(status))
            if isinstance(status, list):
                responses = [
                    s if isinstance(s, httpx.Response) else httpx.Response(status_code=200, json=load_mock_json(s))
                    for s in status
                ]
                return chain(responses, repeat(responses[-1]))
            if isinstance(status, dict):
                return httpx.Response(status_code=200, json=status)
            return httpx.Response(status_code=200, json=load_mock_json("status/baseline.json"))

        def command_handler(request):
            if commands is None:
                return httpx.Response(status_code=404)

            command = json.loads(request.content.decode("utf-8")).get("type")
            if command not in commands:
                return httpx.Response(status_code=404)

            if command not in command_indexes:
                command_indexes[command] = {"current": 0}

            response_data = get_response(commands[command], command_indexes[command])
            return (
                response_data
                if isinstance(response_data, httpx.Response)
                else httpx.Response(status_code=200, json=response_data)
            )

        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            with respx.mock(assert_all_called=False) as mock:
                mock.post(FORDPASS_AUTH_URL).respond(
                    json={"access_token": auth_token, "token_type": "Bearer", "expires_in": 3600}
                )
                mock.post(AUTONOMIC_AUTH_URL).respond(
                    json={"access_token": auth_token, "token_type": "Bearer", "expires_in": 3600}
                )
                mock.get(re.compile(rf"{AUTONOMIC_TELEMETRY_BASE_URL}/*")).side_effect = status_handler()  # type: ignore
                mock.post(re.compile(rf"{AUTONOMIC_COMMAND_BASE_URL}/*")).side_effect = command_handler
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
