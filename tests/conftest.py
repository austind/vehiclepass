"""Fixtures for testing the vehiclepass library using respx."""

import logging
from pathlib import Path
from typing import TypeVar

import pytest
import respx

T = TypeVar("T")

MOCK_RESPONSES_DIR = Path(__file__).parent / "fixtures" / "responses"


def pytest_configure(config):
    """Configure pytest."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")


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
