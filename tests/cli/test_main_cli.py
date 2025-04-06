"""Tests for the main CLI module of HAR to OpenAPI 3 converter."""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

# Import the entire module to make sure coverage is tracked properly
import har_oa3_converter.cli
from har_oa3_converter.cli import main as cli_main
from har_oa3_converter.cli import parse_args as cli_parse_args


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
                        "queryString": [{"name": "page", "value": "1"}],
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
        f.write(json.dumps(sample_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestMainCli:
    """Test the main CLI module."""

    def test_parse_args(self):
        """Test argument parsing for main CLI."""
        # Test with minimal arguments
        args = cli_parse_args(["input.har"])
        assert args.input == "input.har"
        assert args.output == "output.yaml"
        assert args.json is False
        assert args.title == "API generated from HAR"
        assert args.version == "1.0.0"
        assert args.description == "API specification generated from HAR file"
        assert args.servers == []

        # Test with all arguments
        args = cli_parse_args(
            [
                "input.har",
                "-o",
                "output.json",
                "--json",
                "--title",
                "Custom API",
                "--version",
                "2.0.0",
                "--description",
                "Custom description",
                "--server",
                "https://api1.example.com",
                "--server",
                "https://api2.example.com",
            ]
        )
        assert args.input == "input.har"
        assert args.output == "output.json"
        assert args.json is True
        assert args.title == "Custom API"
        assert args.version == "2.0.0"
        assert args.description == "Custom description"
        assert args.servers == ["https://api1.example.com", "https://api2.example.com"]

    def test_main_success(self, sample_har_file):
        """Test successful execution of main CLI."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            output_path = temp_file.name

        try:
            # Run with mock to capture output
            with mock.patch("sys.stdout") as mock_stdout:
                result = cli_main([sample_har_file, "-o", output_path])

                # Check result
                assert result == 0
                assert Path(output_path).exists()
                assert mock_stdout.write.call_count > 0

                # Check output file content
                with open(output_path, "r") as f:
                    content = yaml.safe_load(f)
                    assert "openapi" in content
                    assert content["openapi"] == "3.0.0"
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_main_json_output(self, sample_har_file):
        """Test main CLI with JSON output."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            output_path = temp_file.name

        try:
            # Run with JSON output
            result = cli_main([sample_har_file, "-o", output_path, "--json"])

            # Check result
            assert result == 0
            assert Path(output_path).exists()

            # Check output file content
            with open(output_path, "r") as f:
                content = json.load(f)
                assert "openapi" in content
                assert content["openapi"] == "3.0.0"
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_main_nonexistent_input(self):
        """Test main CLI with nonexistent input file."""
        with mock.patch("sys.stderr"):
            result = cli_main(["nonexistent.har", "-o", "output.yaml"])
            assert result == 1

    def test_main_error_handling(self):
        """Test error handling in main CLI."""
        # Create an invalid HAR file
        with tempfile.NamedTemporaryFile(
            suffix=".har", delete=False, mode="w"
        ) as temp_file:
            temp_file.write("This is not valid JSON")
            invalid_har_path = temp_file.name

        try:
            # Run with invalid input
            with mock.patch("sys.stderr"):
                result = cli_main([invalid_har_path, "-o", "output.yaml"])
                assert result == 1
        finally:
            os.unlink(invalid_har_path)
