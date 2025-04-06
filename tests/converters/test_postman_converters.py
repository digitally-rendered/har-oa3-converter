"""Tests for the Postman format converters."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from har_oa3_converter.converters.format_converter import (
    PostmanToHarConverter,
    PostmanToOpenApi3Converter,
    convert_file,
)


@pytest.fixture
def sample_postman_collection():
    """Sample Postman Collection for testing."""
    return {
        "info": {
            "_postman_id": "test-id",
            "name": "Test API Collection",
            "description": "A collection for testing",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [
            {
                "name": "Users",
                "item": [
                    {
                        "name": "Get Users",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": "https://example.com/api/users?page=1&limit=10",
                                "protocol": "https",
                                "host": ["example", "com"],
                                "path": ["api", "users"],
                                "query": [
                                    {"key": "page", "value": "1"},
                                    {"key": "limit", "value": "10"},
                                ],
                            },
                            "header": [
                                {"key": "Accept", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                            ],
                            "description": "Get a list of users",
                        },
                        "response": [
                            {
                                "name": "Success Response",
                                "originalRequest": {
                                    "method": "GET",
                                    "url": {
                                        "raw": "https://example.com/api/users?page=1&limit=10"
                                    },
                                },
                                "status": "OK",
                                "code": 200,
                                "header": [
                                    {"key": "Content-Type", "value": "application/json"}
                                ],
                                "body": '{"data":[{"id":1,"name":"John Doe"}], "total":1}',
                            }
                        ],
                    },
                    {
                        "name": "Create User",
                        "request": {
                            "method": "POST",
                            "url": {
                                "raw": "https://example.com/api/users",
                                "protocol": "https",
                                "host": ["example", "com"],
                                "path": ["api", "users"],
                            },
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": '{"name":"New User", "email":"user@example.com"}',
                                "options": {"raw": {"language": "json"}},
                            },
                            "description": "Create a new user",
                        },
                        "response": [
                            {
                                "name": "Success Response",
                                "originalRequest": {
                                    "method": "POST",
                                    "url": {"raw": "https://example.com/api/users"},
                                },
                                "status": "Created",
                                "code": 201,
                                "header": [
                                    {"key": "Content-Type", "value": "application/json"}
                                ],
                                "body": '{"id":2,"name":"New User","email":"user@example.com"}',
                            }
                        ],
                    },
                ],
            },
            {
                "name": "Form Example",
                "request": {
                    "method": "POST",
                    "url": "https://example.com/api/form",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/x-www-form-urlencoded",
                        }
                    ],
                    "body": {
                        "mode": "urlencoded",
                        "urlencoded": [
                            {"key": "name", "value": "Test User"},
                            {"key": "email", "value": "test@example.com"},
                        ],
                    },
                },
            },
        ],
    }


@pytest.fixture
def sample_postman_file(sample_postman_collection):
    """Create a sample Postman Collection file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as f:
        json.dump(sample_postman_collection, f)
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestPostmanConverters:
    """Test class for Postman format converters."""

    def test_postman_to_har_conversion(self, sample_postman_file):
        """Test converting Postman Collection to HAR."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".har", mode="w") as f:
            output_path = f.name

        try:
            # Convert Postman to HAR
            converter = PostmanToHarConverter()
            result = converter.convert(sample_postman_file, output_path)

            assert result is not None
            assert "log" in result
            assert "entries" in result["log"]
            assert len(result["log"]["entries"]) >= 3  # Should have at least 3 entries

            # Verify HAR structure
            entries = result["log"]["entries"]

            # Check request methods and URLs
            methods = [entry["request"]["method"] for entry in entries]
            assert "GET" in methods
            assert "POST" in methods

            # Check for query parameters
            get_entry = next(
                entry for entry in entries if entry["request"]["method"] == "GET"
            )
            assert len(get_entry["request"]["queryString"]) > 0
            assert get_entry["request"]["queryString"][0]["name"] == "page"

            # Check for request body in POST request
            post_entries = [
                entry for entry in entries if entry["request"]["method"] == "POST"
            ]
            assert len(post_entries) >= 2

            # At least one POST entry should have a JSON body
            json_post = next(
                (
                    entry
                    for entry in post_entries
                    if "postData" in entry["request"]
                    and "application/json"
                    in entry["request"]["postData"].get("mimeType", "")
                ),
                None,
            )
            assert json_post is not None

            # At least one entry should have a form body
            form_post = next(
                (
                    entry
                    for entry in post_entries
                    if "postData" in entry["request"]
                    and "application/x-www-form-urlencoded"
                    in entry["request"]["postData"].get("mimeType", "")
                ),
                None,
            )
            assert form_post is not None

            # Check output file
            assert os.path.exists(output_path)
            with open(output_path, "r", encoding="utf-8") as f:
                har_data = json.load(f)
                assert har_data == result
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_postman_to_openapi3_conversion(self, sample_postman_file):
        """Test converting Postman Collection to OpenAPI 3."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w") as f:
            output_path = f.name

        try:
            # Convert Postman to OpenAPI 3
            converter = PostmanToOpenApi3Converter()
            result = converter.convert(
                sample_postman_file,
                output_path,
                title="Test API",
                version="1.0.0",
                description="API converted from Postman Collection",
                servers=["https://example.com"],
            )

            assert result is not None
            assert "openapi" in result
            assert result["openapi"] == "3.0.0"
            assert "info" in result
            assert result["info"]["title"] == "Test API"
            assert "paths" in result

            # Check paths
            assert "/api/users" in result["paths"]
            assert "get" in result["paths"]["/api/users"]
            assert "post" in result["paths"]["/api/users"]

            # Check for query parameters
            get_op = result["paths"]["/api/users"]["get"]
            assert "parameters" in get_op
            assert len(get_op["parameters"]) >= 2

            # Check for request body in POST operation
            post_op = result["paths"]["/api/users"]["post"]
            assert "requestBody" in post_op

            # Check output file
            assert os.path.exists(output_path)
            with open(output_path, "r", encoding="utf-8") as f:
                openapi_data = yaml.safe_load(f)
                assert openapi_data == result
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_convert_file_postman_to_har(self, sample_postman_file):
        """Test convert_file function with Postman to HAR conversion."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".har", mode="w") as f:
            output_path = f.name

        try:
            # Use convert_file with schema validation
            result = convert_file(
                sample_postman_file,
                output_path,
                source_format="postman",
                target_format="har",
                validate_schema=True,
            )

            assert result is not None
            assert "log" in result
            assert "entries" in result["log"]

            # Check output file
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_convert_file_postman_to_openapi3(self, sample_postman_file):
        """Test convert_file function with Postman to OpenAPI 3 conversion."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w") as f:
            output_path = f.name

        try:
            # Use convert_file with schema validation
            result = convert_file(
                sample_postman_file,
                output_path,
                source_format="postman",
                target_format="openapi3",
                validate_schema=True,
                title="Test API",
                version="1.0.0",
            )

            assert result is not None
            assert "openapi" in result
            assert "paths" in result

            # Check output file
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
