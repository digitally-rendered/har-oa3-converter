"""Command-line interface for HAR to OpenAPI 3 converter."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import yaml
from yaml import Dumper

from har_oa3_converter.converter import HarToOas3Converter


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.
    
    Args:
        args: Command line arguments (None uses sys.argv)
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Convert HAR files to OpenAPI 3 specification"
    )
    
    parser.add_argument(
        "input",
        help="Path to HAR file"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: output.yaml)",
        default="output.yaml"
    )
    
    parser.add_argument(
        "--json",
        help="Output in JSON format instead of YAML",
        action="store_true"
    )
    
    parser.add_argument(
        "--title",
        help="API title",
        default="API generated from HAR"
    )
    
    parser.add_argument(
        "--version",
        help="API version",
        default="1.0.0"
    )
    
    parser.add_argument(
        "--description",
        help="API description",
        default="API specification generated from HAR file"
    )
    
    parser.add_argument(
        "--server",
        help="Server URL (can be specified multiple times)",
        action="append",
        dest="servers",
        default=[]
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
    
    input_path = parsed_args.input
    output_path = parsed_args.output
    
    # Check if input file exists
    if not Path(input_path).exists():
        print(f"Error: Input file '{input_path}' does not exist", file=sys.stderr)
        return 1
    
    # Configure converter
    info = {
        "title": parsed_args.title,
        "version": parsed_args.version,
        "description": parsed_args.description
    }
    
    servers = []
    for server in parsed_args.servers:
        servers.append({"url": server})
    
    # Convert
    try:
        converter = HarToOas3Converter(info=info, servers=servers)
        spec = converter.convert(input_path)
        
        # Save output
        with open(output_path, "w", encoding="utf-8") as f:
            if parsed_args.json or output_path.endswith(".json"):
                import json
                json.dump(spec, f, indent=2)
            else:
                yaml.dump(spec, f, Dumper=Dumper, default_flow_style=False)
                
        print(f"Converted HAR file to OpenAPI 3 specification: {output_path}")
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
