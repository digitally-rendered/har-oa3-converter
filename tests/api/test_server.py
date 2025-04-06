"""Tests for the API server module."""

import pytest
from fastapi.testclient import TestClient

from har_oa3_converter.api.server import app, custom_openapi, main, parse_args


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


class TestApiServer:
    """Test class for API server."""

    def test_app_exists(self):
        """Test that the FastAPI app exists."""
        assert app is not None
        assert app.title == "HAR to OpenAPI Converter API"

    def test_openapi_schema(self):
        """Test that the OpenAPI schema is generated correctly."""
        schema = custom_openapi()

        assert schema is not None
        assert "servers" in schema
        assert schema["servers"][0]["url"] == "/"
        assert "tags" in schema
        assert len(schema["tags"]) > 0
        assert schema["tags"][0]["name"] == "conversion"

    def test_app_routes(self, client):
        """Test that the app has the expected routes."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "paths" in schema
        assert "/api/formats" in schema["paths"]
        assert "/api/convert/{target_format}" in schema["paths"]

    def test_parse_args_defaults(self):
        """Test parsing arguments with defaults."""
        args = parse_args([])

        assert args.host == "127.0.0.1"
        assert args.port == 8000
        assert args.reload is False

    def test_parse_args_custom(self):
        """Test parsing arguments with custom values."""
        args = parse_args(["--host", "0.0.0.0", "--port", "8080", "--reload"])

        assert args.host == "0.0.0.0"
        assert args.port == 8080
        assert args.reload is True

    def test_main_function(self, monkeypatch):
        """Test the main function with mocked uvicorn.run."""

        # Mock uvicorn.run to avoid actually starting the server
        def mock_run(*args, **kwargs):
            return True

        monkeypatch.setattr("uvicorn.run", mock_run)

        # Call main with test args
        result = main(["--host", "0.0.0.0", "--port", "8080"])

        # Should return 0 for success
        assert result == 0

    def test_cors_headers(self, client):
        """Test that CORS headers are set correctly."""
        response = client.options(
            "/api/formats",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        # The CORS middleware reflects the Origin header rather than using wildcard
        assert response.headers["access-control-allow-origin"] == "http://example.com"
