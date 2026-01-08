"""Pytest configuration for MCP vulnerability tests."""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio as the async backend."""
    return "asyncio"
