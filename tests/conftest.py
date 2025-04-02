"""Fixtures for testing the vehiclepass library."""

import functools
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import pytest

T = TypeVar("T")


def load_mock_json(file_path: str | Path) -> dict[str, Any]:
    """Load mock data from a JSON file.

    Attempts to load the file from the tests/mock_data directory, but if it doesn't exist,
    falls back to the original path.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dict containing the loaded JSON data
    """
    original_path = Path(file_path)
    file_path = Path("tests/mock_data") / file_path
    if not file_path.exists():
        file_path = original_path
        if not file_path.exists():
            raise FileNotFoundError(f"Mock data file not found: {file_path}")

    with open(file_path) as f:
        return json.load(f)


def with_vehicle_mock(
    mock_data: dict[str, Any] | None = None,
    status_file: str | Path | None = None,
    command_responses_files: dict[str, str | Path] | None = None,
    metric_overrides: dict[str, Any] | None = None,
):
    """Decorator to mock Vehicle class with pytest.

    Args:
        mock_data: Dictionary containing inline mock data
        status_file: Path to JSON file with status mock data (includes metrics)
        command_responses_files: Dict mapping command names to response file paths
            e.g. {'remoteStart': 'path/to/start_response.json', 'stop': 'path/to/stop_response.json'}
        metric_overrides: Direct metric value overrides that take precedence
            over values in the status file

    Usage:
        # Using inline data
        @with_vehicle_mock({
            'status': {...},
            'property_values': {'is_running': True}
        })
        def test_function(mocked_vehicle):
            pass

        # Using JSON files
        @with_vehicle_mock(
            status_file='tests/mock_data/vehicle_status.json',
            command_responses_files={
                'remoteStart': 'tests/mock_data/remote_start_response.json',
                'cancelRemoteStart': 'tests/mock_data/cancel_remote_start_response.json'
            }
        )
        def test_function(mocked_vehicle):
            pass
    """
    # Initialize empty mock data dictionary
    combined_data = {"status": {}, "command_responses": {}, "property_values": {}}

    # Load from status file if provided
    if status_file:
        status_data = load_mock_json(status_file)
        combined_data["status"] = status_data

    # Load command response files if provided
    if command_responses_files:
        for command, file_path in command_responses_files.items():
            try:
                response_data = load_mock_json(file_path)
                combined_data.setdefault("command_responses", {})[command] = response_data
            except FileNotFoundError as e:
                import warnings

                warnings.warn(f"Could not load command response file for '{command}': {e}", stacklevel=2)

    # Add metric overrides if provided
    if metric_overrides:
        combined_data["metric_overrides"] = metric_overrides

    # Add inline data, which takes precedence over file data
    if mock_data:
        for key, value in mock_data.items():
            if key in combined_data and isinstance(combined_data[key], dict) and isinstance(value, dict):
                # Merge dictionaries for known categories
                combined_data[key].update(value)
            else:
                # Otherwise just replace
                combined_data[key] = value

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Add the combined mock data as an attribute to the function
        wrapper._vehicle_mock_data = combined_data
        return wrapper

    return decorator


def get_mock_data_dir() -> Path:
    """Get the directory containing mock data JSON files.

    Returns:
        Path to the mock data directory
    """
    # This returns the directory where conftest.py is located
    base_dir = Path(__file__).parent

    # Check several possible locations
    possible_paths = [
        base_dir / "mock_data",
        base_dir / "mocks",
        base_dir / "fixtures",
        base_dir,  # Fallback to the same directory as conftest.py
    ]

    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path

    # If we didn't find an existing directory, create one
    mock_dir = base_dir / "mock_data"
    mock_dir.mkdir(exist_ok=True)
    return mock_dir


@pytest.fixture
def mock_data_dir() -> Path:
    """Fixture providing the path to the mock data directory."""
    return get_mock_data_dir()


@pytest.fixture
def mocked_vehicle(monkeypatch, request):
    """Pytest fixture that creates a mocked Vehicle instance.

    Can be used in multiple ways:
    1. Direct fixture usage:
       def test_something(mocked_vehicle, vehicle_mock_data):
           # Test with mocked_vehicle

    2. With the @with_vehicle_mock decorator:
       @with_vehicle_mock({...mock_data...})
       def test_something(mocked_vehicle):
           # Test with mocked_vehicle pre-configured

    3. With JSON file paths:
       @with_vehicle_mock(
           status_file='tests/mock_data/status.json',
           command_responses_files={
               'remoteStart': 'tests/mock_data/start_response.json'
           }
       )
       def test_something(mocked_vehicle):
           # Test with mocked_vehicle configured from JSON
    """
    from vehiclepass import Vehicle

    # Get mock data from the decorator if it exists
    mock_data = getattr(request.function, "_vehicle_mock_data", {})

    # Or look for the vehicle_mock_data fixture
    if not mock_data and hasattr(request, "getfixturevalue"):
        try:
            mock_data = request.getfixturevalue("vehicle_mock_data")
        except pytest.FixtureLookupError:
            # If no fixture found, use empty mock data
            mock_data = {}

    # Create a real vehicle instance with dummy credentials
    vehicle = Vehicle(username="mock_user", password="mock_pass", vin="MOCK12345")

    # 1. Mock the _request method
    def mock_request(self, method, url, **request_kwargs):
        if "telemetry" in url:
            return mock_data.get("status", {})
        elif "commands" in url:
            command_type = request_kwargs.get("json", {}).get("type")
            return mock_data.get("command_responses", {}).get(command_type, {"status": "unknown"})
        elif "auth" in url:
            return {"access_token": "mock-token-12345"}
        return {}

    monkeypatch.setattr(Vehicle, "_request", mock_request)

    # 2. Mock _get_metric_value
    def mock_get_metric_value(self, metric_name, expected_type=Any):
        # First check if we have a direct metric override
        if "metric_overrides" in mock_data and metric_name in mock_data["metric_overrides"]:
            return mock_data["metric_overrides"][metric_name]

        # Otherwise try to get it from the status
        metrics = self.status.get("metrics", {})
        metric = metrics.get(metric_name, {})
        if not metric:
            # Simulate the error the real method would raise
            from vehiclepass.errors import StatusError

            raise StatusError(f"{metric_name} not found in metrics")

        # Return either the value key or the metric itself
        return metric.get("value", metric)

    monkeypatch.setattr(Vehicle, "_get_metric_value", mock_get_metric_value)

    # 3. Set status directly to avoid real API calls
    vehicle._status = mock_data.get("status", {})

    # 4. Mock any properties directly specified in property_values
    for prop_name, prop_value in mock_data.get("property_values", {}).items():
        if hasattr(Vehicle, prop_name):
            # We need a function factory to capture the current values
            def make_property_getter(value):
                return property(lambda self: value)

            # Monkeypatch the property
            monkeypatch.setattr(Vehicle, prop_name, make_property_getter(prop_value))

    return vehicle


@pytest.fixture
def vehicle_mock_data(mock_data_dir):
    """Fixture providing default mock data for vehicle testing.

    First looks for a default_vehicle_data.json file in the mock_data directory.
    If not found, falls back to the hardcoded defaults.
    """
    # Try to load from a default file if it exists
    default_file = mock_data_dir / "default_vehicle_data.json"
    if default_file.exists():
        try:
            return load_mock_json(default_file)
        except json.JSONDecodeError:
            # If the file exists but isn't valid JSON, log a warning and fall back
            import warnings

            warnings.warn(f"Could not parse default mock data file: {default_file}", stacklevel=2)

    # Fallback to hardcoded defaults
    return {
        "status": {
            "metrics": {
                "outsideTemperature": {"value": 22.0},
                "engineCoolantTemp": {"value": 90.0},
                "ignitionStatus": {"value": "OFF"},
                "remoteStartCountdownTimer": {"value": 900.0},
                "odometer": {"value": 105547.0},
            },
            "events": {
                "remoteStartEvent": {
                    "conditions": {"remoteStartBegan": {"remoteStartDeviceStatus": {"value": "RUNNING"}}}
                }
            },
        },
        "command_responses": {"remoteStart": {"status": "success"}, "cancelRemoteStart": {"status": "success"}},
        "property_values": {"is_running": True, "is_remotely_started": True, "is_ignition_started": False},
    }


# Helper function to create example mock data files
def create_example_mock_files(output_dir: str | Path | None = None):
    """Create example mock data files in the specified directory.

    Args:
        output_dir: Directory where example files should be created.
                    If None, uses the mock_data_dir.
    """
    output_dir = Path(output_dir) if output_dir else get_mock_data_dir()
    output_dir.mkdir(exist_ok=True, parents=True)

    # Example vehicle status (including metrics)
    status_data = {
        "metrics": {
            "outsideTemperature": {"value": 22.0, "updateTime": "2025-04-02T00:58:38Z"},
            "engineCoolantTemp": {"value": 90.0, "updateTime": "2025-04-02T00:58:38Z"},
            "ignitionStatus": {"value": "OFF", "updateTime": "2025-04-02T00:58:38Z"},
            "fuelLevel": {"value": 72.5, "updateTime": "2025-04-02T00:58:38Z"},
            "odometer": {"value": 12345.0, "updateTime": "2025-04-02T00:58:38Z"},
            "remoteStartCountdownTimer": {"value": 0.0, "updateTime": "2025-04-02T00:58:38Z"},
        },
        "events": {
            "remoteStartEvent": {
                "updateTime": "2025-04-02T00:58:38Z",
                "conditions": {
                    "remoteStartEnded": {
                        "remoteStartDeviceStatus": {"updateTime": "2025-04-01T21:54:34Z", "value": "SHUTDOWN"}
                    }
                },
            }
        },
    }

    # Example command responses - now separate files for each command
    remote_start_response = {"status": "success", "requestId": "mock-request-123"}

    cancel_remote_start_response = {"status": "success", "requestId": "mock-request-456"}

    lock_response = {"status": "success", "requestId": "mock-request-789"}

    unlock_response = {"status": "success", "requestId": "mock-request-101"}

    # Example default data (combines all types)
    default_data = {
        "status": status_data,
        "command_responses": {
            "remoteStart": remote_start_response,
            "cancelRemoteStart": cancel_remote_start_response,
            "lock": lock_response,
            "unlock": unlock_response,
        },
        "property_values": {"is_running": False, "is_remotely_started": False, "is_ignition_started": False},
    }

    # Write the files
    with open(output_dir / "vehicle_status.json", "w") as f:
        json.dump(status_data, f, indent=2)

    # Write separate command response files
    with open(output_dir / "remote_start_response.json", "w") as f:
        json.dump(remote_start_response, f, indent=2)

    with open(output_dir / "cancel_remote_start_response.json", "w") as f:
        json.dump(cancel_remote_start_response, f, indent=2)

    with open(output_dir / "lock_response.json", "w") as f:
        json.dump(lock_response, f, indent=2)

    with open(output_dir / "unlock_response.json", "w") as f:
        json.dump(unlock_response, f, indent=2)

    with open(output_dir / "default_vehicle_data.json", "w") as f:
        json.dump(default_data, f, indent=2)

    print(f"Created example mock data files in {output_dir}")
