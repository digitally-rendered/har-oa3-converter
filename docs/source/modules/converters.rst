Converters Module
===============

.. py:module:: har_oa3_converter.converters

The converters module provides functionality for converting between different API formats.

Format Converter
--------------

.. py:module:: har_oa3_converter.converters.format_converter

This module provides a flexible conversion system for different API formats.

.. py:class:: FormatConverter

   Converter for different API formats.

   .. py:method:: convert(data, from_format, to_format)

      Convert data from one format to another.

      :param data: Data to convert
      :type data: dict
      :param from_format: Source format
      :type from_format: str
      :param to_format: Target format
      :type to_format: str
      :return: Converted data
      :rtype: dict

   .. py:method:: detect_format(data)

      Detect the format of the provided data.

      :param data: Data to detect format of
      :type data: dict
      :return: Detected format or None if unknown
      :rtype: Optional[str]

HAR Converter
-----------

.. py:module:: har_oa3_converter.converters.har_converter

This module provides functionality for converting HAR files to other formats.

.. py:function:: convert_har_to_openapi3(har_data, title=None, description=None, version=None, servers=None)

   Convert HAR data to OpenAPI 3.0 specification.

   :param har_data: HAR data to convert
   :type har_data: dict
   :param title: API title
   :type title: Optional[str]
   :param description: API description
   :type description: Optional[str]
   :param version: API version
   :type version: Optional[str]
   :param servers: API servers
   :type servers: Optional[List[str]]
   :return: OpenAPI 3.0 specification
   :rtype: dict

Schema Validation in Converters
----------------------------

All converters use JSON Schema validation to ensure data integrity at each conversion stage. This aligns with the project's requirements that:

1. All models should be represented in JSON_SCHEMA documents
2. All models should be used in tests
3. All models should be used in API responses
4. All models should be used in API requests

This comprehensive validation approach ensures 100% test coverage and robust handling of different data formats.
