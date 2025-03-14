import json
from typing import List

from api_engine.models import EndpointAnalysis, MatchedRequest
from utils.logger import get_logger

# Set up logger
logger = get_logger(__name__)


class HarMatcher:
    """Matches HAR file requests with valuable endpoints identified by analysis."""

    def match(self, har_file: str, analyzed_file: str, output_file: str) -> bool:
        """Match HAR requests with valuable endpoints.

        Args:
            har_file: Path to the HAR file
            analyzed_file: Path to the analyzed endpoints JSON file
            output_file: Output path for matched requests

        Returns:
            bool: True if matching was successful, False otherwise
        """
        try:
            # Load HAR requests
            har_requests = self._load_har_file(har_file)
            logger.info(f"Loaded {len(har_requests)} requests from HAR file")

            # Load valuable endpoints
            valuable_endpoints = self._extract_valuable_endpoints(analyzed_file)
            logger.info(f"Found {len(valuable_endpoints)} valuable endpoints to match")

            # Match endpoints with HAR requests
            matched_requests = self._match_endpoints(har_requests, valuable_endpoints)
            logger.info(f"Found {len(matched_requests)} matched requests")

            # Save matched requests
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    [request.model_dump() for request in matched_requests], f, indent=4
                )

            logger.info(f"Matched requests saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error matching HAR requests: {str(e)}")
            return False

    def _load_har_file(self, har_file: str) -> List[dict]:
        """Load and parse HAR file requests."""
        with open(har_file, "r", encoding="utf-8") as f:
            har_data = json.load(f)

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
