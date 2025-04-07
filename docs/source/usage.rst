Usage
=====

Command Line Interface
--------------------

The HAR to OpenAPI 3 Converter provides a simple command-line interface for converting HAR files to OpenAPI 3 specifications:

.. code-block:: bash

    har2oa3 input.har output.yaml

This will convert the HAR file to an OpenAPI 3 specification in YAML format. You can also specify JSON output:

.. code-block:: bash

    har2oa3 input.har output.json --json

Additional options include:

.. code-block:: bash

    har2oa3 input.har output.yaml \
        --title "My API" \
        --description "API generated from HAR file" \
        --version "1.0.0" \
        --server "https://api.example.com"

Format Conversion CLI
------------------

The package also includes a more flexible format conversion tool:

.. code-block:: bash

    format-converter input.har output.yaml --from-format har --to-format openapi3

Available formats:

- ``har``: HTTP Archive format
- ``openapi3``: OpenAPI 3.0 specification
- ``swagger``: Swagger 2.0 specification
- ``hoppscotch``: Hoppscotch API collection
- ``postman``: Postman collection

The converter can automatically detect formats based on file extensions:

.. code-block:: bash

    format-converter input.har output.yaml  # Formats detected automatically

Python API
---------

You can also use the converter programmatically in your Python code:

.. code-block:: python

    from har_oa3_converter.converter import convert_har_to_oas3

    # Convert HAR to OpenAPI 3
    with open('input.har', 'r') as har_file:
        har_data = json.load(har_file)

    openapi_spec = convert_har_to_oas3(
        har_data,
        title="My API",
        description="API generated from HAR file",
        version="1.0.0",
        servers=["https://api.example.com"]
    )

    # Output as YAML
    with open('output.yaml', 'w') as yaml_file:
        yaml.dump(openapi_spec, yaml_file, sort_keys=False)

RESTful API
----------

The converter can also be run as a RESTful API server:

.. code-block:: bash

    har-oa3-api

This starts a FastAPI server on port 8000 by default. You can then send POST requests to convert formats:

.. code-block:: bash

    curl -X POST -H "Content-Type: application/json" \
         -H "Accept: application/yaml" \
         -d @input.har \
         http://localhost:8000/api/convert/openapi3 > output.yaml

The API server adheres to content negotiation principles, using the Content-Type header to determine the input format and Accept header to determine the output format, making it fully stateless with self-contained request-response cycles.
