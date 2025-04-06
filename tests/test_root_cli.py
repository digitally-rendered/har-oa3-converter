"""Tests for the root CLI module."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Direct import from cli.py to ensure we're testing the right module
import har_oa3_converter.cli
from har_oa3_converter.cli import parse_args, main


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


class TestRootCli:
    """Test class for the root CLI module."""

    def test_parse_args_minimal(self):
        """Test parsing arguments with minimal options."""
        args = parse_args(["input.har"])

        assert args.input == "input.har"
        assert args.output == "output.yaml"
        assert args.json is False
        assert args.title == "API generated from HAR"
        assert args.version == "1.0.0"
        assert args.description == "API specification generated from HAR file"
        assert args.servers == []

    def test_parse_args_with_output(self):
        """Test parsing arguments with custom output."""
        args = parse_args(["input.har", "-o", "custom.yaml"])

        assert args.input == "input.har"
        assert args.output == "custom.yaml"

    def test_parse_args_with_json(self):
        """Test parsing arguments with JSON output option."""
        args = parse_args(["input.har", "--json"])

        assert args.input == "input.har"
        assert args.json is True

    def test_parse_args_with_metadata(self):
        """Test parsing arguments with metadata options."""
        args = parse_args(
            [
                "input.har",
                "--title",
                "Custom API",
                "--version",
                "2.0.0",
                "--description",
                "Custom description",
            ]
        )

        assert args.input == "input.har"
        assert args.title == "Custom API"
        assert args.version == "2.0.0"
        assert args.description == "Custom description"

    def test_parse_args_with_servers(self):
        """Test parsing arguments with server options."""
        args = parse_args(
            [
                "input.har",
                "--server",
                "https://api.example.com",
                "--server",
                "https://staging.example.com",
            ]
        )

        assert args.input == "input.har"
        assert args.servers == [
            "https://api.example.com",
            "https://staging.example.com",
        ]

    def test_main_with_yaml_output(self, sample_har_file):
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

    def test_main_with_json_output(self, sample_har_file):
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

    def test_main_with_custom_options(self, sample_har_file):
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

    def test_main_with_module_execution(self):
        """Test the module's __main__ execution path."""
        # Simulate the __name__ == "__main__" branch
        original_exit = sys.exit
        original_argv = sys.argv

        try:
            # Mock sys.exit and sys.argv
            exit_values = []
            sys.exit = lambda code=0: exit_values.append(code)
            sys.argv = [
                "cli.py",
                "nonexistent.har",
            ]  # Will fail because file doesn't exist

            # Call the __main__ block code
            if (
                hasattr(har_oa3_converter.cli, "__name__")
                and har_oa3_converter.cli.__name__ == "__main__"
            ):
                pass  # Actually executed in module
            else:
                # Simulate the __main__ block
                main_result = main()
                sys.exit(main_result)

            # Check that sys.exit was called with non-zero exit code
            assert len(exit_values) > 0
            assert exit_values[0] != 0

        finally:
            # Restore original functions
            sys.exit = original_exit
            sys.argv = original_argv
