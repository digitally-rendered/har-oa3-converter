"""Command-line interface for format converter."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from har_oa3_converter.format_converter import (
    convert_file,
    get_available_formats,
    get_converter_for_formats,
    guess_format_from_file,
)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Command line arguments (None uses sys.argv)

    Returns:
        Parsed arguments
    """
    available_formats = get_available_formats()
    format_list = ", ".join(available_formats)

    parser = argparse.ArgumentParser(
        description="Convert between API specification formats"
    )

    parser.add_argument("input", help="Path to input file")

    parser.add_argument("output", help="Path to output file")

    parser.add_argument(
        "--from-format",
        help=f"Source format (available: {format_list}). If not specified, will be guessed from input file",
        choices=available_formats,
    )

    parser.add_argument(
        "--to-format",
        help=f"Target format (available: {format_list}). If not specified, will be guessed from output file",
        choices=available_formats,
    )

    # OpenAPI/Swagger specific arguments
    parser.add_argument(
        "--title",
        help="API title (for OpenAPI/Swagger output)",
        default="API Specification",
    )

    parser.add_argument(
        "--version", help="API version (for OpenAPI/Swagger output)", default="1.0.0"
    )

    parser.add_argument(
        "--description",
        help="API description (for OpenAPI/Swagger output)",
        default="API specification generated by format-converter",
    )

    parser.add_argument(
        "--server",
        help="Server URL (can be specified multiple times)",
        action="append",
        dest="servers",
        default=[],
    )

    parser.add_argument("--base-path", help="Base path for API endpoints", default=None)

    parser.add_argument(
        "--list-formats", help="List available formats and exit", action="store_true"
    )

    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI.

    Args:
        args: Command line arguments (None uses sys.argv)

    Returns:
        Exit code
    """
    parsed_args = parse_args(args)

    # Handle listing available formats
    if parsed_args.list_formats:
        formats = get_available_formats()
        print("Available formats:")
        for fmt in formats:
            print(f"  - {fmt}")

        # List available conversions
        print("\nAvailable conversions:")
        for source_format in formats:
            for target_format in formats:
                converter = get_converter_for_formats(source_format, target_format)
                if converter:
                    print(f"  - {source_format} → {target_format}")
        return 0

    input_path = parsed_args.input
    output_path = parsed_args.output

    # Check if input file exists
    if not Path(input_path).exists():
        print(f"Error: Input file '{input_path}' does not exist", file=sys.stderr)
        return 1

    # Parse format arguments
    input_source_format: str = parsed_args.from_format or ""
    input_target_format: str = parsed_args.to_format or ""

    source_format = input_source_format
    if not source_format:
        source_format_guess = guess_format_from_file(input_path)
        if source_format_guess:
            source_format = source_format_guess
        if source_format:
            print(f"Detected source format: {source_format}")
        else:
            print(
                f"Error: Could not detect source format for '{input_path}'. Please specify with --from-format",
                file=sys.stderr,
            )
            return 1

    target_format = input_target_format
    if not target_format:
        # For target format, we first try to guess from the output file extension
        # If that fails, we'll try to determine from the available converters
        target_format_guess = guess_format_from_file(output_path)
        if target_format_guess:
            target_format = target_format_guess
        if target_format:
            print(f"Detected target format: {target_format}")
        else:
            print(
                f"Error: Could not detect target format for '{output_path}'. Please specify with --to-format",
                file=sys.stderr,
            )
            return 1

    # Check if conversion is available
    converter = get_converter_for_formats(source_format, target_format)
    if not converter:
        print(
            f"Error: No converter available for {source_format} to {target_format}",
            file=sys.stderr,
        )
        print("Use --list-formats to see available conversions", file=sys.stderr)
        return 1

    # Create options dict from arguments
    options = {
        "title": parsed_args.title,
        "version": parsed_args.version,
        "description": parsed_args.description,
        "servers": parsed_args.servers,
        "base_path": parsed_args.base_path,
    }

    # Perform conversion
    try:
        print(f"Converting {source_format} to {target_format}...")
        convert_file(input_path, output_path, source_format, target_format, **options)
        print(f"Conversion successful: {output_path}")
        return 0
    except Exception as e:
        print(f"Error during conversion: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
