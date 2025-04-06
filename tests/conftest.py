"""Configuration file for pytest."""

import os

import pytest


def pytest_configure(config):
    """Configure pytest before test execution."""
    # Set environment variable for tests to know they're running in parallel
    if config.getoption("dist", "no") != "no":
        os.environ["PYTEST_XDIST_WORKER"] = "1"


# This is the correct hook for pytest-xdist worker initialization
def pytest_configure_node(node):
    """Configure pytest-xdist worker node."""
    # Log information about parallel execution
    worker_id = node.workerinput["workerid"]
    print(f"Configuring worker {worker_id}")


@pytest.fixture(scope="session")
def worker_id(request):
    """Return the worker ID for the current test session."""
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(autouse=True)
def _setup_test_isolation(worker_id):
    """Set up test isolation for parallel test execution."""
    # Create a unique temporary directory for each worker
    if worker_id != "master":
        temp_dir = f"/tmp/pytest-{worker_id}"
        os.makedirs(temp_dir, exist_ok=True)
        os.environ["TEMP_DIR"] = temp_dir
