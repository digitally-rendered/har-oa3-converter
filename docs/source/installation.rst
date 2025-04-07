Installation
============

You can install the HAR to OpenAPI 3 Converter using pip or from source using Poetry.

Pip Installation
--------------

.. code-block:: bash

    pip install har-oa3-converter

Poetry Installation
-----------------

If you prefer to use Poetry (recommended for development):

.. code-block:: bash

    git clone https://github.com/digitally-rendered/har-oa3-converter.git
    cd har-oa3-converter
    poetry install

Verifying Installation
--------------------

After installation, you can verify that everything is working correctly by running:

.. code-block:: bash

    har2oa3 --help

This should display the help text for the command-line interface.

Supported Python Versions
-----------------------

The HAR to OpenAPI 3 Converter supports Python versions 3.10, 3.11, 3.12, and 3.13.

Please note that earlier Python versions may work but are not officially supported or tested.

Dependencies
-----------

The main dependencies of the project include:

- PyYAML: For YAML parsing and serialization
- jsonschema: For JSON Schema validation
- fastapi (optional): For the HTTP API server
- opentelemetry-api: For telemetry and tracing
- prometheus-client: For metrics collection

All dependencies are automatically installed when you install the package via pip or Poetry.
