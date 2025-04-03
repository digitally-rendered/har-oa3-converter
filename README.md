# HAR to OpenAPI 3 Converter

Convert HAR (HTTP Archive) files to OpenAPI 3 specifications.

## Overview

The HAR to OpenAPI 3 Converter is a Python tool that analyzes HAR files (HTTP Archive format, exported from browser dev tools) and generates OpenAPI 3.0 specifications from them. This is useful for API documentation, testing, and development.

## Features

- Convert HAR files to OpenAPI 3.0 specifications
- Convert between different API formats (HAR, OpenAPI 3, Swagger 2)
- Support for multiple HTTP methods (GET, POST, PUT, DELETE, etc.)
- Automatic parameter detection from query strings and headers
- Request and response body schema generation
- Flexible command-line interface with customization options
- Output in YAML or JSON format
- Format auto-detection based on file extensions

## Installation

```bash
pip install har-oa3-converter
```

Or with Poetry:

```bash
poetry add har-oa3-converter
```

## Usage

### Command Line

#### HAR to OpenAPI Converter

```bash
har2oas input.har -o output.yaml
```

Options:

```
  -o, --output OUTPUT     Output file path (default: output.yaml)
  --json                  Output in JSON format instead of YAML
  --title TITLE           API title
  --version VERSION       API version
  --description DESC      API description
  --server SERVER         Server URL (can be specified multiple times)
```

#### Format Converter

The format converter allows for converting between different API specification formats interchangeably:

```bash
api-convert input.har output.yaml
```

```bash
api-convert input.yaml output.json --from-format openapi3 --to-format swagger
```

Options:

```
  --from-format FORMAT   Source format (e.g., har, openapi3, swagger)
  --to-format FORMAT     Target format (e.g., har, openapi3, swagger)
  --list-formats         List available formats and conversions
  --title TITLE          API title for output
  --version VERSION      API version for output
  --description DESC     API description for output
  --server SERVER        Server URL (can be specified multiple times)
  --base-path PATH       Base path for API endpoints
```

Formats are auto-detected from file extensions when possible. Use `--list-formats` to see all available formats and conversion paths.

### Python API

#### HAR to OpenAPI Converter

```python
from har_oa3_converter.converter import HarToOas3Converter

# Initialize converter
converter = HarToOas3Converter(
    info={
        "title": "My API",
        "version": "1.0.0",
        "description": "API specification generated from HAR file"
    },
    servers=[{"url": "https://api.example.com"}]
)

# Convert HAR file to OpenAPI 3
spec = converter.convert("input.har", "output.yaml")
```

#### Format Converter

```python
from har_oa3_converter.format_converter import convert_file

# Convert HAR to OpenAPI 3
result = convert_file(
    "input.har",
    "output.yaml",
    source_format="har",
    target_format="openapi3",
    title="My API",
    version="1.0.0",
    servers=["https://api.example.com"]
)

# Convert OpenAPI 3 to Swagger 2
result = convert_file(
    "input.yaml",
    "output.json",
    source_format="openapi3",
    target_format="swagger"
)

# With format auto-detection
result = convert_file("input.har", "output.yaml")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/har-oa3-converter.git
cd har-oa3-converter

# Install dependencies with Poetry
poetry install
```

### Testing

Run tests with Poetry and pytest:

```bash
# Run all tests
poetry run pytest

# Run tests with verbose output
poetry run pytest -v

# Run tests for a specific module
poetry run pytest tests/test_converter.py

# Run tests with code coverage
poetry run pytest --cov=har_oa3_converter

# Run tests and output coverage report to HTML
poetry run pytest --cov=har_oa3_converter --cov-report=html
```

You can also run linting and formatting checks with Poetry:

```bash
# Run Black code formatter check
poetry run black --check har_oa3_converter tests

# Apply Black code formatting
poetry run black har_oa3_converter tests

# Run isort import sorting check
poetry run isort --check har_oa3_converter tests

# Apply isort import sorting
poetry run isort har_oa3_converter tests
```

## License

MIT
