import json
from collections import defaultdict
from typing import Dict, List

from api_engine.models import ApiRequest, FilteredEndpoint
from utils.logger import get_logger

logger = get_logger(__name__)


class HarFilter:
    """Filters and processes HAR files to extract API requests."""

    def filter(self, har_file_path: str, request_type: str, output_path: str) -> bool:
        """
        Filter HAR file for specific request types and preprocess the data.

        Args:
            har_file_path: Path to the HAR file
            request_type: HTTP method to filter (GET, POST, etc.)
            output_path: Output file path for filtered requests

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(
                f"Filtering HAR file {har_file_path} for {request_type} requests"
            )

            # Process the HAR file
            grouped_requests = self._process_har_file(har_file_path, request_type)

            # Convert to filtered endpoints for LLM analysis
            filtered_endpoints = self._convert_to_filtered_endpoints(grouped_requests)

            # Save to output file
            with open(output_path, "w") as outfile:
                json.dump(
                    [endpoint.model_dump() for endpoint in filtered_endpoints],
                    outfile,
                    indent=4,
                )

            logger.info(
                f"Filtered {len(filtered_endpoints)} endpoints to {output_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Error filtering HAR file: {str(e)}")
            return False

    def _process_har_file(
        self, har_file_path: str, request_type: str
    ) -> Dict[str, List[ApiRequest]]:
        """
        Process HAR file to extract and group API requests.

        Args:
            har_file_path: Path to the HAR file
            request_type: HTTP method to filter

        Returns:
            Dict mapping endpoints to lists of ApiRequest objects
        """
        with open(har_file_path, "r") as file:
            har_data = json.load(file)

        entries = har_data["log"]["entries"]
        grouped_requests = defaultdict(list)

        for entry in entries:
            request = entry["request"]
            if request["method"] == request_type:
                endpoint = request["url"].split("?")[0]

                # Extract query parameters
                query_params = {}
                for param in request.get("queryString", []):
                    query_params[param["name"]] = param["value"]

                # Extract headers
                headers = {}
                for header in request.get("headers", []):
                    headers[header["name"]] = header["value"]

                # Filter important headers
                filtered_headers = {}
                for k in headers:
                    if k.lower() in ["authorization", "content-type"]:
                        filtered_headers[k] = headers[k]

                # Create API request model
                api_request = ApiRequest(
                    url=endpoint,
                    method=request["method"],
                    query_params=query_params,
                    headers=filtered_headers,
                    post_data=request.get("postData", {}).get("text", None),
                )

                grouped_requests[endpoint].append(api_request)

        return grouped_requests

    def _convert_to_filtered_endpoints(
        self, grouped_requests: Dict[str, List[ApiRequest]]
    ) -> List[FilteredEndpoint]:
        """
        Convert grouped API requests to FilteredEndpoint models.

        Args:
            grouped_requests: Dict mapping endpoints to lists of ApiRequest objects

        Returns:
            List of FilteredEndpoint objects
        """
        filtered_endpoints = []

        for endpoint, requests in grouped_requests.items():
            # Identify unique methods
            methods = list(set(req.method for req in requests))

            # Consolidate query parameters from all requests
            all_params = {}
            for req in requests:
                all_params.update(req.query_params)

            # Use the first request's headers and post data as samples
            sample_headers = requests[0].headers if requests else {}
            sample_post_data = requests[0].post_data if requests else None

            # Create a FilteredEndpoint for this group
            filtered_endpoint = FilteredEndpoint(
                url=endpoint,
                methods=methods,
                params=all_params,
                sample_headers=sample_headers,
                sample_post_data=sample_post_data,
            )

            filtered_endpoints.append(filtered_endpoint)

        return filtered_endpoints
