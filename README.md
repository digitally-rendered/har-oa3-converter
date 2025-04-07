# HAR to OpenAPI 3 Converter

[![Python Tests](https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/python-tests.yml/badge.svg)](https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/python-tests.yml)
[![Code Quality](https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/code-quality.yml/badge.svg)](https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/code-quality.yml)
[![codecov](https://codecov.io/gh/digitally-rendered/har-oa3-converter/branch/main/graph/badge.svg)](https://codecov.io/gh/digitally-rendered/har-oa3-converter)
[![Coverage](https://raw.githubusercontent.com/digitally-rendered/har-oa3-converter/main/badges/coverage.svg)](https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/python-tests.yml)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/python-compatibility.yml)

Convert HAR (HTTP Archive) files to OpenAPI 3 specifications with comprehensive schema validation and multiple format support.

## Overview

The HAR to OpenAPI 3 Converter is a Python tool that analyzes HAR files (HTTP Archive format, exported from browser dev tools) and generates OpenAPI 3.0 specifications from them. This is useful for API documentation, testing, mock server generation, and API-driven development.

Built with robust schema validation and adherence to OpenAPI standards, this converter ensures high-quality API specifications from real-world HTTP interaction data.

## Features

- Convert HAR files to OpenAPI 3.0 specifications with schema validation
- Convert between different API formats (HAR, OpenAPI 3, Swagger 2, Hoppscotch)
- Support for multiple HTTP methods (GET, POST, PUT, DELETE, PATCH, OPTIONS, etc.)
- Automatic parameter detection from query strings, headers, and path parameters
- Request and response body schema generation with comprehensive type mapping
- Flexible command-line interface with extensive customization options
- RESTful API for conversions via HTTP requests
- Output in YAML or JSON format with content negotiation support
- Format auto-detection based on file extensions and content inspection
- Full JSON Schema validation for request/response models
- Stateless processing for scalable deployments
- Extensive test coverage (95%+) ensuring reliability

## Supported Formats

The converter supports the following formats:

| Format | Description | File Extensions |
|--------|-------------|-----------------|
| HAR | HTTP Archive format from browser dev tools | .har |
| OpenAPI 3 | Modern API specification format | .yaml, .yml, .json |
| Swagger 2 | Legacy API specification format | .yaml, .yml, .json |
| Hoppscotch | Hoppscotch Collection format | .json |

Supported conversion paths:

- HAR → OpenAPI 3.0
- OpenAPI 3.0 → Swagger 2.0
- Swagger 2.0 → OpenAPI 3.0
- Hoppscotch → OpenAPI 3.0

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

The primary CLI tool converts HAR files to OpenAPI 3 specifications:

```bash
# Basic usage - convert HAR to YAML (default)
har2oa3 input.har -o output.yaml

# Convert HAR to JSON format
har2oa3 input.har -o output.json --json

# Add API metadata
har2oa3 input.har -o output.yaml \
  --title "My API" \
  --version "1.0.0" \
  --description "API generated from HAR capture"

# Specify multiple servers
har2oa3 input.har -o output.yaml \
  --server "https://api.example.com/v1" \
  --server "https://staging-api.example.com/v1"

# Validate the output with schema validation
har2oa3 input.har -o output.yaml --validate
```

Options:

```
  -o, --output OUTPUT     Output file path (default: output.yaml)
  --json                  Output in JSON format instead of YAML
  --title TITLE           API title
  --version VERSION       API version
  --description DESC      API description
  --server SERVER         Server URL (can be specified multiple times)
  --validate              Validate the output against OpenAPI 3 schema
  --base-path PATH        Base path for API endpoints
  --skip-auth             Skip authentication headers in the output
```

#### Format Converter

The generic format converter allows for converting between different API specification formats interchangeably:

```bash
# Auto-detect formats based on file extensions
api-convert input.har output.yaml

# Explicitly specify formats for conversion
api-convert input.yaml output.json --from-format openapi3 --to-format swagger

# List all available formats and conversion paths
api-convert --list-formats

# Complex conversion with metadata
api-convert input.openapi.json output.swagger.json \
  --title "Updated API" \
  --version "2.0.0" \
  --description "Converted from OpenAPI 3 to Swagger 2" \
  --server "https://api.example.com" \
  --base-path "/api/v2"

# Convert HAR to OpenAPI and validate
api-convert input.har output.yaml --validate

# Convert Hoppscotch Collection to OpenAPI 3
api-convert hoppscotch_collection.json api_spec.yaml --from-format hoppscotch --to-format openapi3
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
  --validate             Validate output against format schema
  --skip-auth            Skip authentication headers in output
  --verbose              Enable verbose output
```

Formats are auto-detected from file extensions when possible. Use `--list-formats` to see all available formats and conversion paths.

**Example format list output:**

```
Available formats:
- har: HTTP Archive format (.har)
- openapi3: OpenAPI 3.0 specification (.yaml, .yml, .json)
- swagger: Swagger 2.0 specification (.yaml, .yml, .json)
- hoppscotch: Hoppscotch Collection format (.json)

Available conversions:
- har → openapi3: Convert HAR to OpenAPI 3.0
- openapi3 → swagger: Convert OpenAPI 3.0 to Swagger 2.0
- swagger → openapi3: Convert Swagger 2.0 to OpenAPI 3.0
- hoppscotch → openapi3: Convert Hoppscotch Collection to OpenAPI 3.0
```

#### API Server

The project includes a FastAPI-based API server that provides conversion capabilities through a RESTful API:

```bash
# Start the API server (default: http://127.0.0.1:8000)
api-server

# Configure host and port
api-server --host 0.0.0.0 --port 8080

# Enable auto-reload for development
api-server --reload

## Docker

The HAR to OpenAPI 3 Converter can be run in a Docker container for consistent environments across platforms.

### Building the Docker Image

```bash
# Build the Docker image
./scripts/build_docker.sh

# Or build manually
docker build -t har-oa3-converter:latest .
```

### Running the Converter in Docker

```bash
# Basic usage - convert HAR to YAML
docker run --rm -v $(pwd):/data har-oa3-converter:latest format -i /data/input.har -o /data/output.yaml

# With options
docker run --rm -v $(pwd):/data har-oa3-converter:latest format \
  -i /data/input.har \
  -o /data/output.yaml \
  --title "Docker API" \
  --version "1.0.0"# Step 1: Set up Rancher Desktop
  ./scripts/setup_rancher_desktop.sh

  # Step 2: Verify Docker is ready for testing
  ./scripts/verify_docker_for_testing.sh

  # Step 3: Run your Docker tests
  ./scripts/run_tests_in_docker.sh

# Using the API server in Docker
docker run --rm -p 8080:8080 har-oa3-converter:latest api-server --host 0.0.0.0 --port 8080
```

### Testing with Docker

We provide comprehensive testing capabilities within Docker to ensure consistent test environments:

```bash
# Run all tests in Docker with coverage, HTML and JSON reports, and parallel execution
./scripts/run_tests_in_docker.sh

# Run specific tests in Docker
./scripts/run_tests_in_docker.sh tests/converters/

# Run Docker-specific tests only
pytest tests/docker/test_docker_functionality.py -v

# Run API endpoint tests against the containerized API server
./scripts/run_api_tests_in_docker.sh
```

The Docker tests validate:

1. Application functionality within containers
2. Command-line interface operation
3. HAR to OpenAPI conversion accuracy
4. Test coverage requirements (targeting 100%)
5. Proper reporting via pytest-html and pytest-json-report
6. Parallel test execution with pytest-xdist
7. Complete API endpoint validation (for the RESTful API server)

Test reports from Docker execution are available in the `docker-reports` directory after running the tests.

### API Testing with Docker

The API tests (`tests/docker/test_docker_api.py`) specifically validate the containerized API server by:

1. Launching the API server in a Docker container
2. Testing all API endpoints through HTTP requests
3. Validating proper response formats based on Accept headers
4. Ensuring schema validation using the centralized JSON schemas
5. Testing error handling for invalid inputs
6. Verifying that conversions work correctly through the API

API tests follow the same quality standards as all other tests:

- 100% test coverage requirement
- Comprehensive JSON schema validation for all requests/responses
- Proper HTTP status code checking
- Content negotiation testing (JSON/YAML output formats)
- Detailed HTML and JSON reporting

Run the API tests with full reporting:

```bash
./scripts/run_api_tests_in_docker.sh
```

API test reports are available in the `docker-reports/api-tests` directory.

# Specify log level
api-server --log-level debug
```

The API server provides the following endpoints:

- `GET /` - Root endpoint with welcome message
- `GET /health` - Health check endpoint
- `GET /api/formats` - Lists all available conversion formats
- `POST /api/convert/{target_format}` - Converts a document to the specified format

The conversion endpoint supports:
- Content negotiation via Accept headers (JSON/YAML)
- Form data for conversion options
- Multipart file uploads
- Stateless operation for scalability

**Example using curl:**

```bash
# Convert HAR to OpenAPI 3 and get JSON response
curl -X POST "http://localhost:8000/api/convert/openapi3" \
  -H "Accept: application/json" \
  -F "file=@sample.har" \
  -F "title=My API" \
  -F "version=1.0.0"

# Convert HAR to OpenAPI 3 and get YAML response
curl -X POST "http://localhost:8000/api/convert/openapi3" \
  -H "Accept: application/yaml" \
  -F "file=@sample.har"

# Convert OpenAPI 3 to Swagger with custom options
curl -X POST "http://localhost:8000/api/convert/swagger" \
  -H "Accept: application/json" \
  -F "file=@openapi.yaml" \
  -F "base_path=/api/v2" \
  -F "skip_validation=true"

# Convert Hoppscotch collection to OpenAPI 3
curl -X POST "http://localhost:8000/api/convert/openapi3" \
  -H "Accept: application/json" \
  -F "file=@hoppscotch_collection.json" \
  -F "title=Hoppscotch API" \
  -F "version=1.0.0"

# List available formats
curl -X GET "http://localhost:8000/api/formats" \
  -H "Accept: application/json"

# Check server health
curl -X GET "http://localhost:8000/health"
```

Visit the API documentation at `http://localhost:8000/docs` when the server is running to explore the complete API schema, request/response models, and try the API directly from the interactive Swagger UI.

### Python API

#### HAR to OpenAPI Converter

```python
from har_oa3_converter.converter import HarToOas3Converter

# Initialize converter with metadata
converter = HarToOas3Converter(
    info={
        "title": "My API",
        "version": "1.0.0",
        "description": "API specification generated from HAR file"
    },
    servers=[{"url": "https://api.example.com"}]
)

# Convert HAR file to OpenAPI 3 YAML
spec = converter.convert("input.har", "output.yaml")

# Process HAR data from already loaded object
import json
with open("input.har", "r") as f:
    har_data = json.load(f)
    # Convert HAR data to OpenAPI 3 spec
    spec = converter.convert_from_dict(har_data)
    # Output as dictionary
    oas3_dict = spec.to_dict()
    # Output as JSON string
    oas3_json = spec.to_json()
    # Output as YAML string
    oas3_yaml = spec.to_yaml()
    # Save to file
    spec.save("output.yaml")
```

#### Format Converter

```python
# Generic converter for various formats
from har_oa3_converter.format_converter import convert_file, get_available_formats, get_converter_for_formats

# List available formats and converters
formats = get_available_formats()
print(f"Available formats: {formats}")

# Get specific converter for a format pair
converter = get_converter_for_formats("har", "openapi3")

# Get Hoppscotch to OpenAPI 3 converter
hoppscotch_converter = get_converter_for_formats("hoppscotch", "openapi3")

# Example using Hoppscotch converter
from har_oa3_converter.converters.formats.hoppscotch_to_openapi3 import HoppscotchToOpenApi3Converter

# Initialize converter
hoppscotch_converter = HoppscotchToOpenApi3Converter()

# Convert Hoppscotch collection file to OpenAPI 3
result = hoppscotch_converter.convert("hoppscotch_collection.json", "openapi3_spec.yaml")

# Convert HAR to OpenAPI 3 with options
result = convert_file(
    "input.har",
    "output.yaml",
    source_format="har",
    target_format="openapi3",
    title="My API",
    version="1.0.0",
    description="API generated from HAR capture",
    servers=["https://api.example.com"],
    base_path="/api/v1",
    validate=True
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

# In-memory conversion
import json
import yaml

# Load HAR data
with open("input.har", "r") as f:
    har_data = json.load(f)

# Initialize converter and convert directly
from har_oa3_converter.converters.format_converter import HarToOpenApi3Converter
converter = HarToOpenApi3Converter()
oas3_spec = converter.convert_dict(har_data)

# Save result
with open("output.yaml", "w") as f:
    yaml.dump(oas3_spec, f)
```

#### Using File Handler API

```python
# Working with different file formats
from har_oa3_converter.utils.file_handler import FileHandler

# Create a file handler
file_handler = FileHandler()

# Read different formats
har_data = file_handler.read_file("input.har")  # Reads as JSON
yaml_data = file_handler.read_file("input.yaml")  # Reads as YAML

# Write different formats
file_handler.write_file("output.json", data, format="json")
file_handler.write_file("output.yaml", data, format="yaml")

# Auto-detect format from extension
data = file_handler.read_file("input.yaml")  # Auto-detects YAML
file_handler.write_file("output.json", data)  # Auto-detects JSON
```

#### RESTful API Integration

```python
# Using the API programmatically
import requests
import json

# Convert HAR to OpenAPI 3 via API
with open("input.har", "rb") as har_file:
    files = {"file": ("input.har", har_file)}
    data = {
        "title": "My API",
        "version": "1.0.0",
        "description": "API generated from HAR file"
    }

    # Get response as JSON
    response = requests.post(
        "http://localhost:8000/api/convert/openapi3",
        files=files,
        data=data,
        headers={"Accept": "application/json"}
    )

    # Save the result
    if response.status_code == 200:
        with open("output.json", "w") as f:
            json.dump(response.json(), f, indent=2)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/har-oa3-converter.git
cd har-oa3-converter

# Install dependencies with Poetry
poetry install

# Install development dependencies
poetry install --with dev
```

### Testing

The project targets 100% test coverage with comprehensive tests for all functionality. Every converter and feature is thoroughly tested to ensure reliability and correctness.

```bash
# Run all tests
poetry run pytest

# Run tests with verbose output
poetry run pytest -v

# Run tests for a specific module
poetry run pytest tests/test_converter.py

# Run specific converter tests
poetry run pytest tests/converters/test_hoppscotch_to_openapi3.py -v

# Run tests with code coverage
poetry run pytest --cov=har_oa3_converter

# Generate HTML coverage report
poetry run pytest --cov=har_oa3_converter --cov-report=html:reports/coverage

# Generate both HTML and JSON reports
poetry run pytest --cov=har_oa3_converter --cov-report=html:reports/coverage \
  --html=reports/pytest.html --json-report --json-report-file=reports/pytest.json

# Run tests in parallel for faster execution
poetry run pytest -xvs -n auto
```

#### Test Structure

Tests are organized by component and feature:

- **Converter Tests**: Each format converter has dedicated tests (HAR, Postman, Hoppscotch, etc.)
- **Schema Tests**: Validate all JSON schemas used for validation
- **API Tests**: Test the RESTful API endpoints
- **CLI Tests**: Verify command-line functionality
- **Integration Tests**: Test end-to-end workflows
- **Docker Tests**: Validate containerized functionality

All models used in the converters are represented in JSON Schema documents and thoroughly tested with various input combinations to ensure robust handling of different API specifications.

### Code Quality

The project maintains high code quality standards through automated tools and best practices:

```bash
# Format code with Black
poetry run black har_oa3_converter tests

# Run linter
poetry run pylint har_oa3_converter tests

# Check type hints with mypy
poetry run mypy har_oa3_converter
```

### Building and Publishing

```bash
# Build package
poetry build

# Publish to PyPI
poetry publish

# Build and publish in one step
poetry publish --build
```

## Schema Validation

The converter uses JSON Schema validation for all models and conversions. Schemas are stored in a central file for consistency:

```python
from har_oa3_converter.schemas.json_schemas import SCHEMAS

# Available schemas
har_schema = SCHEMAS["har"]
openapi3_schema = SCHEMAS["openapi3"]
swagger_schema = SCHEMAS["swagger"]

# Validate data against schema
from jsonschema import validate
validate(instance=my_data, schema=openapi3_schema)
```

## API Request and Response Models

All API requests and responses use Pydantic models with schema validation:

```python
from har_oa3_converter.api.models import ConversionResponse, ErrorResponse, ConversionOptions

# Create conversion options
options = ConversionOptions(
    title="My API",
    version="1.0.0",
    description="API generated from HAR file",
    servers=["https://api.example.com"],
    base_path="/api/v1",
    skip_validation=False
)

# Response model with validation
response = ConversionResponse(
    openapi="3.0.0",
    info={
        "title": "My API",
        "version": "1.0.0"
    },
    paths={}
)

# Convert to dict for serialization
response_dict = response.model_dump()
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

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

### Bazel Build System

This project also includes a Bazel build system for managing the build and publishing processes:

```bash
# Install Bazel if you don't have it already
brew install bazelisk  # on macOS (uses Bazelisk which manages Bazel versions)

# Build the project using Bazel
bazel build //...

# Run tests
bazel test //...

# Run the command-line tools through Bazel
bazel run //:har2oa3 -- input.har -o output.yaml
bazel run //:api-convert -- input.har output.yaml
bazel run //:api-server

# Use Bazel scripts for Poetry operations
./bazel/build.sh      # Build the Poetry package
./bazel/publish.sh    # Publish to PyPI (requires POETRY_PYPI_TOKEN_PYPI env var)
```

Bazel offers several advantages:

- Hermetic builds with better reproducibility
- Incremental, parallel builds for better performance
- Integration with other build systems and CI/CD pipelines
- Consistent build environment across different machines

## Contributing

Contributions are welcome! This project uses GitHub Actions for CI/CD pipeline that handles testing and publishing.

### How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Open a pull request

### CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

- Tests run automatically on push and pull requests
- Publishing to PyPI happens automatically when a version tag is pushed

For more details, see:
- [CONTRIBUTING.md](CONTRIBUTING.md) - Comprehensive contribution guidelines
- [docs/ci_cd_pipeline.md](docs/ci_cd_pipeline.md) - Detailed CI/CD pipeline documentation

### Release Process

To release a new version:

1. Update version in `pyproject.toml`
2. Commit changes
3. Create and push a version tag: `git tag v0.1.1 && git push origin v0.1.1`
4. GitHub Actions will automatically test and publish to PyPI

## License

MIT
# GPG Signing Test
# Another GPG Signing Test
