API Reference
============

Core Converter Module
------------------

The core functionality of the HAR to OpenAPI 3 Converter is provided by the ``har_oa3_converter.converter`` module.

The main function for converting HAR files to OpenAPI 3 specifications is:

.. code-block:: python

    from har_oa3_converter.converter import convert_har_to_oas3

    openapi_spec = convert_har_to_oas3(
        har_data,
        title="My API",
        description="API generated from HAR file",
        version="1.0.0",
        servers=["https://api.example.com"]
    )

Format Converters
---------------

The ``har_oa3_converter.converters.format_converter`` module provides a flexible conversion system that can convert between various API formats:

.. code-block:: python

    from har_oa3_converter.converters.format_converter import FormatConverter

    converter = FormatConverter()
    converted_data = converter.convert(
        source_data,
        from_format="har",
        to_format="openapi3"
    )

Available formats:

- ``har``: HTTP Archive format
- ``openapi3``: OpenAPI 3.0 specification
- ``swagger``: Swagger 2.0 specification
- ``hoppscotch``: Hoppscotch API collection
- ``postman``: Postman collection

REST API Server
------------

The ``har_oa3_converter.api.server`` module provides a FastAPI-based REST API for converting formats:

.. code-block:: python

    from har_oa3_converter.api.server import create_app

    app = create_app()

    # Run with uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

The API endpoints respect content negotiation, using the Content-Type header to determine the input format and Accept header to determine the output format. This makes the API fully stateless with self-contained request-response cycles.

Logging and Telemetry
------------------

The ``har_oa3_converter.utils.logging`` module provides structured logging capabilities:

.. code-block:: python

    from har_oa3_converter.utils.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Processing HAR file")

    # With structured data
    logger.info("API endpoint processing", extra={
        "method": "GET",
        "path": "/api/users",
        "status_code": 200
    })

The ``har_oa3_converter.utils.telemetry`` module provides OpenTelemetry integration for distributed tracing and Prometheus metrics:

.. code-block:: python

    from har_oa3_converter.utils.telemetry import init_telemetry, traced, get_tracer

    # Initialize telemetry
    init_telemetry(service_name="har-oa3-converter")

    # Use tracing decorator
    @traced()
    def process_data(data):
        # Function code here
        pass

    # Manual span creation
    with get_tracer().start_as_current_span("custom_operation") as span:
        span.set_attribute("request.method", "GET")
        # Operation code here
