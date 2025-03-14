import json
from typing import Dict, List, Tuple

from api_engine.models import EndpointAnalysis, MatchedRequest
from utils.logger import get_logger

# Set up logger
logger = get_logger(__name__)


class HarMatcher:
    """Matches HAR file requests with valuable endpoints identified by analysis."""

    def match(
        self,
        har_data: Dict,
        analyzed_endpoints: List[EndpointAnalysis],
        output_file: str = None,
    ) -> Tuple[bool, List[MatchedRequest]]:
        """Match HAR requests with valuable endpoints.

        Args:
            har_data: HAR data as dictionary
            analyzed_endpoints: List of analyzed endpoints
            output_file: Optional output path for matched requests

        Returns:
            tuple: (success, matched_requests)
        """
        try:
            # Load HAR requests
            har_requests = self._extract_har_requests(har_data)
            logger.info(f"Extracted {len(har_requests)} requests from HAR data")

            # Extract valuable endpoints
            valuable_endpoints = [endpoint.url for endpoint in analyzed_endpoints]
            logger.info(f"Found {len(valuable_endpoints)} valuable endpoints to match")

            # Match endpoints with HAR requests
            matched_requests = self._match_endpoints(har_requests, valuable_endpoints)
            logger.info(f"Found {len(matched_requests)} matched requests")

            # Optionally save matched requests
            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(
                        [request.model_dump() for request in matched_requests],
                        f,
                        indent=4,
                    )
                logger.info(f"Matched requests saved to {output_file}")

            return True, matched_requests
        except Exception as e:
            logger.error(f"Error matching HAR requests: {str(e)}")
            return False, []

    def _extract_har_requests(self, har_data: Dict) -> List[dict]:
        """Extract requests from HAR data."""
        requests = []
        for entry in har_data["log"]["entries"]:
            request = entry["request"]
            response = entry["response"]

            requests.append(
                {
                    "url": request["url"].split("?")[0],
                    "method": request["method"],
                    "headers": {h["name"]: h["value"] for h in request["headers"]},
                    "status_code": response["status"],
                }
            )

        return requests

    def _extract_valuable_endpoints(self, file_path: str) -> List[str]:
        """Extract valuable endpoints from analysis results."""
        with open(file_path, "r", encoding="utf-8") as f:
            endpoints_data = json.load(f)

        # Convert to EndpointAnalysis objects if needed for validation
        endpoints = [EndpointAnalysis(**endpoint) for endpoint in endpoints_data]
        valuable_endpoints = [endpoint.url for endpoint in endpoints]
        return valuable_endpoints

    def _match_endpoints(
        self, har_requests: List[dict], valuable_endpoints: List[str]
    ) -> List[MatchedRequest]:
        """Match HAR requests with valuable endpoints."""
        matched_requests = []

        for request in har_requests:
            for endpoint in valuable_endpoints:
                if request["url"].startswith(endpoint):
                    # Create a MatchedRequest object using the model
                    matched_request = MatchedRequest(
                        url=request["url"],
                        method=request["method"],
                        headers=request["headers"],
                        status_code=request["status_code"],
                    )
                    matched_requests.append(matched_request)
                    break

        return matched_requests
