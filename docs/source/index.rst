HAR to OpenAPI 3 Converter Documentation
====================================

.. image:: https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/python-tests.yml/badge.svg
   :target: https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/python-tests.yml
   :alt: Python Tests

.. image:: https://raw.githubusercontent.com/digitally-rendered/har-oa3-converter/main/badges/coverage.svg
   :target: https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/python-tests.yml
   :alt: Coverage

.. image:: https://raw.githubusercontent.com/digitally-rendered/har-oa3-converter/main/badges/python-versions.svg
   :target: https://github.com/digitally-rendered/har-oa3-converter/actions/workflows/python-compatibility.yml
   :alt: Python Versions

The HAR to OpenAPI 3 Converter is a Python tool that analyzes HAR files (HTTP Archive format, exported from browser dev tools) and generates OpenAPI 3.0 specifications from them.

Features
--------

- Convert HAR files to OpenAPI 3.0 specifications with schema validation
- Convert between different API formats (HAR, OpenAPI 3, Swagger 2, Hoppscotch)
- Support for multiple HTTP methods
- Automatic parameter detection from query strings, headers, and path parameters
- Request and response body schema generation
- Flexible command-line interface
- RESTful API for conversions via HTTP requests
- Output in YAML or JSON format with content negotiation support
- Format auto-detection based on file extensions and content inspection
- Full JSON Schema validation for request/response models
- Stateless processing for scalable deployments
- Extensive test coverage (targeting 100%)

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api
   cli
   schemas
   development

API Reference
------------

This documentation provides detailed information about the modules and classes in the HAR to OpenAPI 3 Converter library.

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
