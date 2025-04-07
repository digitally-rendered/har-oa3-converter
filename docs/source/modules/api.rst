API Module
=========

.. py:module:: har_oa3_converter.api

The API module provides a RESTful API server for the HAR to OpenAPI 3 converter.

Server
------

.. py:module:: har_oa3_converter.api.server

This module provides a FastAPI server with endpoints for converting between different API formats.

.. py:function:: create_app()

   Create and configure the FastAPI application.

   :return: Configured FastAPI application
   :rtype: fastapi.FastAPI

Models
------

.. py:module:: har_oa3_converter.api.models

This module provides data models for the API, which are represented in JSON_SCHEMA documents for validation and documentation.

Request and Response Handling
--------------------------

The API endpoints follow these principles:

- Use JSON Schema validation for request and response bodies
- Stateless processing (all requests are self-contained)
- Content negotiation via HTTP headers (Accept for output format, Content-Type for input format)
- Schema validation is integrated with content type negotiation
