"""Tests for the HAR to OpenAPI CLI module."""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from har_oa3_converter.cli.har_to_oas_cli import main, parse_args


@pytest.fixture
def sample_har_file():
    """Create a sample HAR file for testing."""
    sample_data = {
        "log": {
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
                        "statusText": "OK",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "content": {
                            "mimeType": "application/json",
                            "text": '{"data": []}',
                        },
                    },
                }
            ]
        }
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix=".har") as f:
        f.write(json.dumps(sample_data).encode("utf-8"))
        file_path = f.name

    yield file_path

    # Cleanup
    os.unlink(file_path)


class TestHarToOasCli:
    """Test class for HAR to OpenAPI CLI module."""

    def test_parse_args(self):
        """Test argument parsing."""
        args = parse_args(["input.har"])
        assert args.input == "input.har"
        assert args.output == "output.yaml"
        assert not args.json

        args = parse_args(["input.har", "-o", "custom.json", "--json"])
        assert args.input == "input.har"
        assert args.output == "custom.json"
        assert args.json

        args = parse_args(
            [
                "input.har",
                "--title",
                "Custom API",
                "--version",
                "2.0.0",
                "--description",
                "Custom description",
                "--server",
                "https://api.example.com",
                "--server",
                "https://dev-api.example.com",
            ]
        )
        assert args.title == "Custom API"
        assert args.version == "2.0.0"
        assert args.description == "Custom description"
        assert args.servers == [
            "https://api.example.com",
            "https://dev-api.example.com",
        ]

    def test_main_yaml_output(self, sample_har_file):
        """Test main function with YAML output."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
            output_path = f.name

        try:
            exit_code = main([sample_har_file, "-o", output_path])

            assert exit_code == 0
            assert Path(output_path).exists()

            # Verify YAML content
            with open(output_path, "r", encoding="utf-8") as f:
                spec = yaml.safe_load(f)
                assert "openapi" in spec
                assert "paths" in spec
                assert "/api/users" in spec["paths"]

        finally:
            # Cleanup
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_main_json_output(self, sample_har_file):
        """Test main function with JSON output."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            output_path = f.name

        try:
            exit_code = main([sample_har_file, "-o", output_path, "--json"])

            assert exit_code == 0
            assert Path(output_path).exists()

            # Verify JSON content
            with open(output_path, "r", encoding="utf-8") as f:
                spec = json.load(f)
                assert "openapi" in spec
                assert "paths" in spec
                assert "/api/users" in spec["paths"]

        finally:
            # Cleanup
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_main_nonexistent_input(self):
        """Test main function with nonexistent input file."""
        exit_code = main(["nonexistent.har"])
        assert exit_code == 1
