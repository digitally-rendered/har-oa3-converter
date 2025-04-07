Converter Module
==============

.. py:module:: har_oa3_converter.converter

The main converter module provides functionality for converting HAR files to OpenAPI 3 specifications.

.. code-block:: python

   from har_oa3_converter.converter import convert_har_to_oas3

   openapi_spec = convert_har_to_oas3(
       har_data,
       title="My API",
       description="API Documentation",
       version="1.0.0"
   )

Module Functions
--------------

.. py:function:: convert_har_to_oas3(har_data, title=None, description=None, version=None, servers=None)

   Convert HAR data to OpenAPI 3.0 Specification.

   :param dict har_data: The HAR data to convert
   :param str title: Optional API title
   :param str description: Optional API description
   :param str version: Optional API version
   :param list servers: Optional list of API servers
   :return: The OpenAPI 3.0 specification as a dictionary
   :rtype: dict
