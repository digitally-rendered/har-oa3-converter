"""Tests for the main CLI module."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from har_oa3_converter.cli import main, parse_args


@pytest.fixture
def sample_har_file():
    """Create a sample HAR file for testing."""
    sample_data = {
        "log": {
            "version": "1.2",
            "creator": {"name": "Browser DevTools", "version": "1.0"},
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/api/users",
                        "queryString": [],
                        "headers": [],
                    },
                    "response": {
                        "status": 200,
                        "headers": [],
                        "content": {
                            "mimeType": "application/json",
                            "text": '{"data": []}',
                        },
                    },
                }
            ],
        }
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(sample_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestCliModule:
    """Test class for main CLI module."""

    def test_parse_args_minimal(self):
        """Test parsing arguments with minimal options."""
        args = parse_args(["input.har"])

        assert args.input == "input.har"
        assert args.output == "output.yaml"
        assert args.json is False
        assert args.title == "API generated from HAR"
        assert args.version == "1.0.0"
        assert args.description == "API specification generated from HAR file"
        assert hasattr(args, "servers")
        assert isinstance(args.servers, list)

    def test_parse_args_full(self):
        """Test parsing arguments with all options."""
        args = parse_args(
            [
                "input.har",
                "-o",
                "output.json",
                "--json",
                "--title",
                "Test API",
                "--version",
                "2.0.0",
                "--description",
                "Test Description",
                "--server",
                "https://api.example.com",
                "--server",
                "https://staging.example.com",
            ]
        )

        assert args.input == "input.har"
        assert args.output == "output.json"
        assert args.json is True
        assert args.title == "Test API"
        assert args.version == "2.0.0"
        assert args.description == "Test Description"
        assert args.servers == [
            "https://api.example.com",
            "https://staging.example.com",
        ]

    def test_main_yaml_output(self, sample_har_file):
        """Test main function with YAML output."""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        output_file.close()

        try:
            # Run main with sample HAR file
            exit_code = main([sample_har_file, "-o", output_file.name])

            # Check exit code
            assert exit_code == 0

            # Check that output file was created
            assert os.path.exists(output_file.name)

            # Check that output is valid YAML with OpenAPI 3.0 content
            with open(output_file.name, "r") as f:
                content = yaml.safe_load(f)

            assert content is not None
            assert "openapi" in content
            assert content["openapi"] == "3.0.0"
            assert "paths" in content
            assert "/api/users" in content["paths"]
        finally:
            # Cleanup
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)

    def test_main_json_output(self, sample_har_file):
        """Test main function with JSON output."""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        output_file.close()

        try:
            # Run main with sample HAR file and JSON output
            exit_code = main([sample_har_file, "-o", output_file.name, "--json"])

            # Check exit code
            assert exit_code == 0

            # Check that output file was created
            assert os.path.exists(output_file.name)

            # Check that output is valid JSON with OpenAPI 3.0 content
            with open(output_file.name, "r") as f:
                content = json.load(f)

            assert content is not None
            assert "openapi" in content
            assert content["openapi"] == "3.0.0"
        finally:
            # Cleanup
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)

    def test_main_with_options(self, sample_har_file):
        """Test main function with custom options."""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        output_file.close()

        try:
            # Run main with sample HAR file and custom options
            exit_code = main(
                [
                    sample_har_file,
                    "-o",
                    output_file.name,
                    "--title",
                    "Custom API",
                    "--version",
                    "2.0.0",
                    "--description",
                    "Custom Description",
                    "--server",
                    "https://custom.example.com",
                ]
            )

            # Check exit code
            assert exit_code == 0

            # Check that output file was created with custom options
            with open(output_file.name, "r") as f:
                content = yaml.safe_load(f)

            assert content["info"]["title"] == "Custom API"
            assert content["info"]["version"] == "2.0.0"
            assert content["info"]["description"] == "Custom Description"
            assert content["servers"][0]["url"] == "https://custom.example.com"
        finally:
            # Cleanup
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)

    def test_main_error_invalid_input(self):
        """Test main function with invalid input file."""
        # Create a temporary invalid file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
            f.write(b"invalid content")
            invalid_file = f.name

        try:
            # Run main with invalid file
            exit_code = main([invalid_file])

            # Should return non-zero exit code for error
            assert exit_code != 0
        finally:
            # Cleanup
            os.unlink(invalid_file)

    def test_main_error_nonexistent_input(self):
        """Test main function with nonexistent input file."""
        # Run main with nonexistent file
        exit_code = main(["nonexistent.har"])

        # Should return non-zero exit code for error
        assert exit_code != 0
