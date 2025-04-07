Command Line Interface
====================

The HAR to OpenAPI 3 Converter provides several command-line interfaces for different conversion needs.

har2oa3 - HAR to OpenAPI 3 Conversion
----------------------------------

The main CLI tool is ``har2oa3``, which provides a focused interface for converting HAR files to OpenAPI 3 specifications:

.. code-block:: bash

    har2oa3 input.har output.yaml [options]

Options:

- ``--json``: Output in JSON format instead of YAML
- ``--title TEXT``: API title
- ``--description TEXT``: API description
- ``--version TEXT``: API version
- ``--server TEXT``: API server URL (can be specified multiple times)
- ``--help``: Show help message and exit

Examples:

.. code-block:: bash

    # Basic conversion
    har2oa3 input.har output.yaml

    # With custom metadata
    har2oa3 input.har output.yaml \
        --title "My API" \
        --description "API from HAR" \
        --version "1.0.0" \
        --server "https://api.example.com"

    # Output as JSON
    har2oa3 input.har output.json --json

format-converter - Multi-Format Conversion
---------------------------------------

For more advanced format conversion between various API formats, use the ``format-converter`` tool:

.. code-block:: bash

    format-converter input_file output_file [options]

Options:

- ``--from-format FORMAT``: Source format (har, openapi3, swagger, hoppscotch, postman)
- ``--to-format FORMAT``: Target format (har, openapi3, swagger, hoppscotch, postman)
- ``--list-formats``: List available formats and conversions
- ``--help``: Show help message and exit

Examples:

.. code-block:: bash

    # Convert HAR to OpenAPI 3
    format-converter input.har output.yaml --from-format har --to-format openapi3

    # Convert OpenAPI 3 to Swagger 2
    format-converter input.yaml output.json --from-format openapi3 --to-format swagger

    # Use automatic format detection (based on file extensions)
    format-converter input.har output.yaml

    # List available formats
    format-converter --list-formats

har-oa3-api - REST API Server
--------------------------

Start the HTTP API server for format conversion via REST endpoints:

.. code-block:: bash

    har-oa3-api [options]

Options:

- ``--host TEXT``: Host to bind the server to (default: 0.0.0.0)
- ``--port INTEGER``: Port to bind the server to (default: 8000)
- ``--log-level TEXT``: Logging level (default: info)
- ``--help``: Show help message and exit

Examples:

.. code-block:: bash

    # Start server with default settings
    har-oa3-api

    # Start on a specific port with debug logging
    har-oa3-api --port 9000 --log-level debug

Environment Variables
------------------

The CLI tools respect the following environment variables:

- ``HAR_OA3_LOG_LEVEL``: Set the logging level (debug, info, warning, error)
- ``OTEL_SERVICE_NAME``: Name of the service for telemetry reporting
- ``OTEL_EXPORTER``: Type of exporter for OpenTelemetry (console, otlp)
- ``PROMETHEUS_METRICS_PORT``: Port for exposing Prometheus metrics
