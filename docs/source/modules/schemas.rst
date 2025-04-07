Schemas Module
=============

.. py:module:: har_oa3_converter.schemas

The schemas module provides JSON Schema definitions for all data models used in the application, aligning with the requirement that all models should be represented in JSON_SCHEMA documents.

JSON Schemas
-----------

.. py:module:: har_oa3_converter.schemas.json_schemas

This module manages the loading and validation of JSON schema definitions.

.. py:function:: get_schema(schema_name)

   Get a JSON schema by name.

   :param schema_name: Name of the schema (e.g., "har", "openapi3")
   :type schema_name: str
   :return: JSON schema as a dictionary
   :rtype: dict

.. py:function:: register_schema(schema_name, schema_dict)

   Register a custom JSON schema.

   :param schema_name: Name for the schema
   :type schema_name: str
   :param schema_dict: JSON schema as a dictionary
   :type schema_dict: dict

Schema Validation
---------------

.. py:module:: har_oa3_converter.schemas.schema_validator

This module provides validation functionality for JSON schema validation.

.. py:function:: validate_schema(data, schema)

   Validate data against a JSON schema.

   :param data: Data to validate
   :type data: dict
   :param schema: Schema name or schema dictionary
   :type schema: Union[str, dict]
   :return: Validation result object
   :rtype: ValidationResult

.. py:class:: ValidationResult

   Result of a schema validation operation.

   .. py:attribute:: is_valid
      :type: bool

      Whether the validation was successful.

   .. py:attribute:: error
      :type: Optional[str]

      Error message if validation failed.

   .. py:attribute:: error_path
      :type: Optional[str]

      Path to the error in the validated data.
