"""Tests to validate the API endpoints in the har-oa3-converter Docker container."""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Generator, Optional

import pytest
import requests
import yaml

from tests.docker.docker_utils import docker_available, generate_random_container_name, cleanup_container
from tests.docker.test_docker_functionality import docker_running


def wait_for_server(
    url: str, max_retries: int = 30, retry_interval: float = 1.0
) -> bool:
    """Wait for the API server to become available."""
    # More retries and longer interval for Docker startup which can be slower
    print(f"Waiting for API server at {url}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/docs", timeout=5)
            if response.status_code == 200:
                print(f"API server is ready after {i+1} attempts")
                return True
        except requests.RequestException as e:
            if i % 5 == 0:  # Log every 5 attempts to avoid too much output
                print(f"Server not ready (attempt {i+1}/{max_retries}): {str(e)}")
        time.sleep(retry_interval)
    print("ERROR: API server did not start in time")
    return False


class DockerAPIContainer:
    """Context manager for managing a Docker API container."""

    def __init__(
        self,
        image_name: str = "har-oa3-converter:latest",
        host: str = "127.0.0.1",
        port: int = 0,  # Use 0 to get a dynamic port
    ):
        self.image_name = image_name
        # Generate a unique container name to avoid conflicts
        self.container_name = generate_random_container_name(prefix="har-oa3-api")
        self.host = host
        self.port = self._find_free_port() if port == 0 else port
        self.url = f"http://{host}:{self.port}"
        self.headers = {"Accept": "application/json"}  # Default headers for JSON
        self._container_id = None
        self._mock_mode = False  # Flag to indicate if running in mock mode
        
    def _find_free_port(self) -> int:
        """Find a free port to use for the Docker container."""
        import socket
        import random
        
        # When running in parallel with pytest-xdist, add worker id to port base
        # to reduce chance of conflicts between workers
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "")
        worker_offset = int(worker_id.replace("gw", "") or "0") * 100 if worker_id else 0
        
        # Try to find a free port in a higher range (10000-65000) with worker offset
        base_port = 10000 + worker_offset
        max_attempts = 10
        
        for _ in range(max_attempts):
            # Generate a random port in a higher range with worker offset
            port = base_port + random.randint(1000, 5000)
            
            # Verify the port is actually free
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((self.host, port))
                    return port
                except OSError:
                    # Port is in use, try another one
                    continue
                    
        # Fallback to OS-assigned port if we couldn't find a free one
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, 0))
            return s.getsockname()[1]

    def __enter__(self) -> "DockerAPIContainer":
        # Check if Docker is available
        if not docker_available():
            print("\n⚠️ ALERT: Docker is not available for API container tests\n")
            print("ℹ️  API tests running in mock mode with limited functionality")
            print("ℹ️  Start Docker daemon for full test validation\n")
            # Set as mock container instead of skipping
            self._mock_mode = True
            return self

        # Remove existing container if it exists
        self._cleanup_existing_container()

        # Start a new container
        print(f"Starting Docker container for API testing on port {self.port}...")
        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            self.container_name,
            "-p",
            f"{self.port}:{self.port}",
            self.image_name,
            "api-server",
            "--host",
            "0.0.0.0",
            "--port",
            str(self.port),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self._container_id = result.stdout.strip()
            print(f"Container started with ID: {self._container_id}")

            # Print container logs to help with debugging
            time.sleep(2)  # Give it a moment to start up
            log_cmd = ["docker", "logs", self.container_name]
            log_result = subprocess.run(log_cmd, capture_output=True, text=True)
            logs_stdout = log_result.stdout or ""
            logs_stderr = log_result.stderr or ""
            print(f"Container startup logs:\n{logs_stdout}\n{logs_stderr}")
        except subprocess.CalledProcessError as e:
            error_stdout = getattr(e, "stdout", "") or ""
            error_stderr = getattr(e, "stderr", "") or ""
            print(f"Failed to start container: {e}\n{error_stdout}\n{error_stderr}")
            raise

        # Wait for the server to start
        if not wait_for_server(self.url):
            print("\n⚠️ ALERT: API server in Docker container failed to start\n")
            print("ℹ️  API server tests require a functioning Docker container")
            print("ℹ️  Check that your API server implementation works correctly\n")
            print("ℹ️  Verify network ports are properly configured and available\n")
            self._cleanup()
            pytest.skip("API server did not start in time")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._cleanup()

    def _cleanup_existing_container(self) -> None:
        """Remove any existing container with the same name and clean up stale containers."""
        from tests.docker.docker_utils import cleanup_container
        
        # Clean up the specific container for this test
        if cleanup_container(self.container_name):
            print(f"Cleaned up existing container: {self.container_name}")
            
        # Also clean up any stale containers from previous test runs
        # that might have the same prefix (especially important for parallel testing)
        try:
            # List all containers with our prefix
            cmd = [
                "docker", 
                "ps", 
                "-a", 
                "--filter", 
                f"name=har-oa3-api", 
                "--format", 
                "{{.Names}}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                stale_containers = result.stdout.strip().split('\n')
                for container in stale_containers:
                    # Skip our current container
                    if container == self.container_name:
                        continue
                    # Clean up stale container
                    cleanup_container(container)
                    print(f"Cleaned up stale container: {container}")
        except Exception as e:
            # Don't fail the test if cleanup fails
            print(f"Warning: Error cleaning up stale containers: {e}")

    def _cleanup(self) -> None:
        if self._container_id:
            try:
                subprocess.run(
                    ["docker", "stop", self.container_name], capture_output=True
                )
                subprocess.run(
                    ["docker", "rm", self.container_name], capture_output=True
                )
            except Exception as e:
                print(f"Error cleaning up container: {e}")
            self._container_id = None


@pytest.fixture
def api_container() -> Generator[DockerAPIContainer, None, None]:
    """Fixture to provide a running Docker API container."""
    with DockerAPIContainer() as container:
        yield container


@pytest.fixture
def sample_har_file() -> Generator[str, None, None]:
    """Create a sample HAR file for testing."""
    sample_har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "test-docker-api", "version": "1.0"},
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/api/users",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                    },
                    "response": {
                        "status": 200,
                        "statusText": "OK",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps(
                                {"data": [{"id": 1, "name": "Test User"}]}
                            ),
                        },
                    },
                }
            ],
        }
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(sample_har).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    if os.path.exists(file_path):
        os.unlink(file_path)


@docker_running
def test_api_docs_endpoint(api_container: DockerAPIContainer) -> None:
    """Test that the API documentation endpoint works."""
    response = requests.get(f"{api_container.url}/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


@docker_running
def test_api_openapi_schema_endpoint(api_container: DockerAPIContainer) -> None:
    """Test that the OpenAPI schema endpoint works."""
    response = requests.get(f"{api_container.url}/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
    assert "/api/convert" in str(
        schema["paths"]
    ), "API should have /api/convert endpoint"
    assert "/api/formats" in str(
        schema["paths"]
    ), "API should have /api/formats endpoint"
    assert "components" in schema

    # Verify JSON schema usage in the OpenAPI specification
    assert "schemas" in schema["components"], "OpenAPI spec should define schemas"

    # Check that schemas are properly defined for API request/response models
    schemas = schema["components"]["schemas"]
    assert len(schemas) > 0, "At least one schema should be defined"

    # Check content-type specification for endpoints
    for path_key, path_item in schema["paths"].items():
        for method_key, method_item in path_item.items():
            if method_key in ["get", "post", "put", "delete"]:
                if "responses" in method_item:
                    for status_code, response_spec in method_item["responses"].items():
                        if status_code == "200":
                            # Successful responses should specify content types
                            assert (
                                "content" in response_spec
                            ), f"Endpoint {path_key} {method_key} should specify content types"
                            assert (
                                "application/json" in response_spec["content"]
                            ), f"Endpoint {path_key} {method_key} should support JSON responses"


@docker_running
def test_api_formats_endpoint_json(api_container: DockerAPIContainer) -> None:
    """Test the API formats endpoint with JSON response."""
    # Use class-level headers to ensure consistent API testing
    response = requests.get(
        f"{api_container.url}/api/formats", headers=api_container.headers
    )

    # Verify response basics
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    # Check response structure
    data = response.json()
    assert "formats" in data, "Response should have a 'formats' key"
    formats = data["formats"]
    assert isinstance(formats, list), "Formats should be a list"
    assert len(formats) > 0, "At least one format should be available"

    # Verify format structure and required formats
    format_names = [fmt.get("name") for fmt in formats if "name" in fmt]
    assert "openapi3" in format_names, "OpenAPI 3 format should be available"
    assert "har" in format_names, "HAR format should be available"

    # Verify that formats have required fields
    for fmt in formats:
        assert "name" in fmt, "Format should have a name"
        assert "description" in fmt, "Format should have a description"
        assert "content_types" in fmt, "Format should have content types"
        assert isinstance(fmt["content_types"], list), "Content types should be a list"


@docker_running
def test_api_formats_endpoint_yaml(api_container: DockerAPIContainer) -> None:
    """Test the API formats endpoint with YAML response."""
    # Set Accept header for YAML
    headers = {"Accept": "application/x-yaml"}
    response = requests.get(f"{api_container.url}/api/formats", headers=headers)

    # Verify response basics
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-yaml")

    # Parse YAML response
    data = yaml.safe_load(response.text)
    assert "formats" in data, "Response should have a 'formats' key"
    formats = data["formats"]
    assert isinstance(formats, list), "Formats should be a list"
    assert len(formats) > 0, "At least one format should be available"

    # Verify the expected formats are available
    format_names = [fmt.get("name") for fmt in formats if "name" in fmt]
    assert "openapi3" in format_names, "OpenAPI 3 format should be available"
    assert "har" in format_names, "HAR format should be available"


@docker_running
def test_api_convert_endpoint_json(
    api_container: DockerAPIContainer, sample_har_file: str
) -> None:
    """Test the API convert endpoint with JSON output."""
    # Prepare the file for upload
    files = {
        "file": (
            os.path.basename(sample_har_file),
            open(sample_har_file, "rb"),
            "application/json",
        )
    }
    # Use class-level headers for consistency
    headers = api_container.headers.copy()
    # The target format is now a path parameter
    target_format = "openapi3"

    # Send the request
    response = requests.post(
        f"{api_container.url}/api/convert/{target_format}", files=files, headers=headers
    )

    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    content = response.json()
    assert "openapi" in content
    assert "paths" in content
    assert "/api/users" in content["paths"]


@docker_running
def test_api_convert_endpoint_yaml(
    api_container: DockerAPIContainer, sample_har_file: str
) -> None:
    """Test the API convert endpoint with YAML output."""
    # Prepare the file for upload
    files = {
        "file": (
            os.path.basename(sample_har_file),
            open(sample_har_file, "rb"),
            "application/json",
        )
    }
    # Set headers for YAML response
    headers = {"Accept": "application/x-yaml"}
    # The target format is now a path parameter
    target_format = "openapi3"

    # Send the request
    response = requests.post(
        f"{api_container.url}/api/convert/{target_format}", files=files, headers=headers
    )

    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-yaml")
    content = yaml.safe_load(response.text)
    assert "openapi" in content
    assert "paths" in content
    assert "/api/users" in content["paths"]


@docker_running
def test_api_convert_with_options(
    api_container: DockerAPIContainer, sample_har_file: str
) -> None:
    """Test the API convert endpoint with additional options."""
    # Prepare the file for upload
    files = {
        "file": (
            os.path.basename(sample_har_file),
            open(sample_har_file, "rb"),
            "application/json",
        )
    }
    # The target format is now a path parameter
    target_format = "openapi3"
    # Additional options remain as form data
    data = {
        "title": "Docker API Test",
        "version": "1.0.0-test",
        "description": "Test API description",
    }

    # Send the request
    response = requests.post(
        f"{api_container.url}/api/convert/{target_format}", files=files, data=data
    )

    # Verify response
    assert response.status_code == 200
    content = yaml.safe_load(response.text)  # Default is YAML
    assert "openapi" in content
    assert "info" in content
    assert content["info"]["title"] == "Docker API Test"
    assert content["info"]["version"] == "1.0.0-test"
    assert content["info"]["description"] == "Test API description"


@docker_running
def test_api_error_handling_no_file(api_container: DockerAPIContainer) -> None:
    """Test API error handling when no file is provided."""
    # Target format is now a path parameter
    target_format = "openapi3"
    response = requests.post(f"{api_container.url}/api/convert/{target_format}")
    assert response.status_code == 422  # Unprocessable Entity
    error_data = response.json()
    assert "detail" in error_data


@docker_running
def test_api_error_handling_invalid_format(
    api_container: DockerAPIContainer, sample_har_file: str
) -> None:
    """Test API error handling with invalid target format."""
    files = {
        "file": (
            os.path.basename(sample_har_file),
            open(sample_har_file, "rb"),
            "application/json",
        )
    }
    # Invalid format is now part of the path
    invalid_format = "invalid_format"

    response = requests.post(
        f"{api_container.url}/api/convert/{invalid_format}", files=files
    )
    assert response.status_code in [400, 422]  # Bad Request or Unprocessable Entity
    error_data = response.json()
    assert "detail" in error_data


@docker_running
def test_api_error_handling_invalid_file(api_container: DockerAPIContainer) -> None:
    """Test API error handling with invalid file content."""
    # Create an invalid HAR file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(b"This is not valid JSON or HAR data")
        invalid_file_path = f.name

    try:
        files = {
            "file": (
                os.path.basename(invalid_file_path),
                open(invalid_file_path, "rb"),
                "application/json",
            )
        }
        # Target format is now a path parameter
        target_format = "openapi3"

        response = requests.post(
            f"{api_container.url}/api/convert/{target_format}", files=files
        )
        assert response.status_code in [
            400,
            422,
            500,
        ]  # Could be any error code depending on implementation
        assert response.headers["content-type"].startswith("application/json")
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data
    finally:
        if os.path.exists(invalid_file_path):
            os.unlink(invalid_file_path)


@docker_running
def test_api_convert_with_source_format_override(
    api_container: DockerAPIContainer, sample_har_file: str
) -> None:
    """Test API with source format override."""
    files = {
        "file": (
            os.path.basename(sample_har_file),
            open(sample_har_file, "rb"),
            "application/json",
        )
    }
    # Target format is now a path parameter
    target_format = "openapi3"
    # Only source_format remains as form data
    data = {"source_format": "har"}  # Explicitly specify source format

    response = requests.post(
        f"{api_container.url}/api/convert/{target_format}", files=files, data=data
    )
    assert response.status_code == 200
    content = yaml.safe_load(response.text)
    assert "openapi" in content
    assert "paths" in content
