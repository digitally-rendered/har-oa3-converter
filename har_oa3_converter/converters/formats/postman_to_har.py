"""Converter from Postman Collection to HAR."""

import json
import os
from typing import Any, Dict, List, Optional

from har_oa3_converter.converters.formats.base import FormatConverter
from har_oa3_converter.utils.file_handler import FileHandler


class PostmanToHarConverter(FormatConverter):
    """Converter from Postman Collection to HAR."""

    @classmethod
    def get_source_format(cls) -> str:
        """Get the source format this converter handles.

        Returns:
            Source format name
        """
        return "postman"

    @classmethod
    def get_target_format(cls) -> str:
        """Get the target format this converter produces.

        Returns:
            Target format name
        """
        return "har"

    def convert(
        self, source_path: str, target_path: Optional[str] = None, **options
    ) -> Dict[str, Any]:
        """Convert Postman Collection to HAR format.

        Args:
            source_path: Path to Postman Collection file
            target_path: Path to output HAR file (optional)
            options: Additional options

        Returns:
            HAR data as dictionary
        """
        # Read Postman Collection file using FileHandler to handle different formats properly
        file_handler = FileHandler()
        postman_data = file_handler.load(source_path)

        # Create HAR structure
        har_data = {
            "log": {
                "version": "1.2",
                "creator": {
                    "name": "HAR Converter",
                    "version": "1.0.0",
                },
                "entries": [],
            }
        }

        # Process Postman Collection items
        self._process_postman_items(postman_data, har_data["log"]["entries"])

        # Write to target file if specified
        if target_path:
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            # Use FileHandler to save the file in the appropriate format
            file_handler.save(har_data, target_path)

        return har_data

    def _process_postman_items(
        self, postman_data: Dict[str, Any], entries: List[Dict[str, Any]]
    ) -> None:
        """Process Postman Collection items and add them to HAR entries.

        Args:
            postman_data: Postman Collection data
            entries: HAR entries list to populate
        """
        # Get items from collection
        items = postman_data.get("item", [])
        if not items:
            return

        # Process items recursively
        self._process_items(items, entries)

    def _process_items(
        self, items: List[Dict[str, Any]], entries: List[Dict[str, Any]]
    ) -> None:
        """Process Postman items recursively.

        Args:
            items: List of Postman items
            entries: HAR entries list to populate
        """
        for item in items:
            # Check if this is a folder (has items)
            if "item" in item and isinstance(item["item"], list):
                # Process folder items recursively
                self._process_items(item["item"], entries)
            elif "request" in item:
                # This is a request item, convert it to HAR entry
                entry = self._convert_request_to_entry(item)
                if entry:
                    entries.append(entry)

    def _convert_request_to_entry(
        self, item: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Convert a Postman request to a HAR entry.

        Args:
            item: Postman request item

        Returns:
            HAR entry or None if conversion failed
        """
        request_data = item.get("request", {})
        if not request_data:
            return None

        # Extract request details
        method = request_data.get("method", "GET")
        url_obj = request_data.get("url", {})

        # Handle different URL formats in Postman
        url = ""
        if isinstance(url_obj, str):
            url = url_obj
        elif isinstance(url_obj, dict):
            # Build URL from components
            protocol = url_obj.get("protocol", "https")
            host = url_obj.get("host", [])
            if isinstance(host, list):
                host = ".".join(host)
            path = url_obj.get("path", [])
            if isinstance(path, list):
                path = "/".join(path)
            elif isinstance(path, str):
                path = path.lstrip("/")
            url = f"{protocol}://{host}/{path}"

            # Add query parameters
            query_params = self._convert_query_params(url_obj)
            if query_params:
                query_string = "&".join([f"{p['name']}={p['value']}" for p in query_params])
                url = f"{url}?{query_string}"

        # Create HAR entry
        entry = {
            "startedDateTime": "2023-01-01T00:00:00.000Z",  # Placeholder
            "time": 0,  # Placeholder
            "request": {
                "method": method,
                "url": url,
                "httpVersion": "HTTP/1.1",
                "cookies": [],
                "headers": self._convert_headers(request_data.get("header", [])),
                "queryString": self._convert_query_params(url_obj),
                "postData": {
                    "mimeType": "",
                    "text": "",
                },
                "headersSize": -1,
                "bodySize": -1,
            },
            "response": {
                "status": 200,  # Placeholder
                "statusText": "OK",  # Placeholder
                "httpVersion": "HTTP/1.1",
                "cookies": [],
                "headers": [],
                "content": {
                    "size": 0,
                    "mimeType": "application/json",
                    "text": "",
                },
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": -1,
            },
            "cache": {},
            "timings": {
                "send": 0,
                "wait": 0,
                "receive": 0,
            },
        }

        # Add request body if present
        if "body" in request_data:
            self._add_request_body(entry["request"], request_data["body"])

        # Add example response if available
        if "response" in item and isinstance(item["response"], list) and item["response"]:
            self._add_example_response(entry["response"], item["response"][0])

        return entry

    def _convert_headers(
        self, headers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert Postman headers to HAR format.

        Args:
            headers: Postman headers list

        Returns:
            HAR headers list
        """
        result = []
        for header in headers:
            if "key" in header and "value" in header:
                result.append({
                    "name": header["key"],
                    "value": header["value"],
                })
        return result

    def _convert_query_params(
        self, url_obj: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert Postman URL query params to HAR format.

        Args:
            url_obj: Postman URL object

        Returns:
            HAR query string parameters
        """
        result = []
        query = url_obj.get("query", [])
        for param in query:
            if "key" in param and "value" in param:
                result.append({
                    "name": param["key"],
                    "value": param["value"],
                })
        return result

    def _add_request_body(
        self, request: Dict[str, Any], body_data: Dict[str, Any]
    ) -> None:
        """Add body data to HAR request.

        Args:
            request: HAR request object
            body_data: Postman body data
        """
        mode = body_data.get("mode", "")
        if not mode:
            return

        # Set mime type based on mode
        mime_type = "text/plain"
        if mode == "raw":
            # Check if there's a content-type header
            for header in request.get("headers", []):
                if header["name"].lower() == "content-type":
                    mime_type = header["value"]
                    break
            
            # Default to JSON if it looks like JSON
            raw_data = body_data.get("raw", "")
            if raw_data.strip().startswith("{") or raw_data.strip().startswith("["):
                mime_type = "application/json"
            
            request["postData"] = {
                "mimeType": mime_type,
                "text": raw_data,
            }
        elif mode == "urlencoded":
            mime_type = "application/x-www-form-urlencoded"
            params = []
            for param in body_data.get("urlencoded", []):
                if "key" in param and "value" in param:
                    params.append({
                        "name": param["key"],
                        "value": param["value"],
                    })
            
            request["postData"] = {
                "mimeType": mime_type,
                "params": params,
                "text": "&".join([f"{p['name']}={p['value']}" for p in params]),
            }
        elif mode == "formdata":
            mime_type = "multipart/form-data"
            params = []
            for param in body_data.get("formdata", []):
                if "key" in param and "value" in param:
                    params.append({
                        "name": param["key"],
                        "value": param["value"],
                    })
            
            request["postData"] = {
                "mimeType": mime_type,
                "params": params,
            }

    def _add_example_response(
        self, response: Dict[str, Any], example: Dict[str, Any]
    ) -> None:
        """Add example response data to HAR response.

        Args:
            response: HAR response object
            example: Postman example response
        """
        # Set status code and text
        response["status"] = example.get("code", 200)
        response["statusText"] = example.get("status", "OK")

        # Set headers
        response["headers"] = self._convert_headers(example.get("header", []))

        # Set response body
        body = example.get("body", "")
        mime_type = "text/plain"

        # Try to determine mime type from headers
        for header in response["headers"]:
            if header["name"].lower() == "content-type":
                mime_type = header["value"]
                break

        # Default to JSON if it looks like JSON
        if body and isinstance(body, str):
            if body.strip().startswith("{") or body.strip().startswith("["):
                mime_type = "application/json"

        response["content"] = {
            "size": len(body) if body else 0,
            "mimeType": mime_type,
            "text": body,
        }
