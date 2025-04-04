"""Tests for the format_cli module default values."""

import pytest

from har_oa3_converter.cli.format_cli import parse_args


def test_format_cli_default_values():
    """Test the default values used in format_cli module."""
    args = parse_args(["input.har", "output.yaml"])
    
    # Print the actual values for debugging
    print(f"Title: {args.title!r}")
    print(f"Description: {args.description!r}")
    
    # Verify against expected values
    assert args.title == "API Specification"
    assert args.description == "API specification generated by format-converter"
