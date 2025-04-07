JSON Schema Validation
====================

The HAR to OpenAPI 3 Converter uses JSON Schema extensively for validation and model definition as mandated by the project requirements.

Schema Organization
-----------------

All JSON schemas are defined in the ``har_oa3_converter/schemas`` directory and are used throughout the application for:

1. Model representation in both requests and responses
2. Runtime validation of input and output data
3. Documentation generation
4. Test scenarios and validation

Core Schemas
-----------

The core schemas include:

- HAR (HTTP Archive) schema definition
- OpenAPI 3.0 schema definition
- Swagger 2.0 schema definition
- Internal conversion models

Using Schemas for Validation
--------------------------

The converter uses JSON Schema validation to ensure that all inputs and outputs conform to their respective specifications:

.. code-block:: python

    from har_oa3_converter.converters.schema_validator import validate_schema

    # Validate HAR data against the HAR schema
    validation_result = validate_schema(har_data, schema="har")

    if not validation_result.is_valid:
        print(f"Validation error: {validation_result.error}")

Schema Loading
------------

The schemas are loaded from JSON files at runtime:

.. code-block:: python

    from har_oa3_converter.schemas.json_schemas import get_schema

    # Get the OpenAPI 3.0 schema
    openapi_schema = get_schema("openapi3")

Extending Schemas
--------------

You can extend the built-in schemas or add custom ones for specialized validation needs:

.. code-block:: python

    from har_oa3_converter.schemas.json_schemas import register_schema

    # Register a custom schema
    register_schema("custom_format", custom_schema_dict)
