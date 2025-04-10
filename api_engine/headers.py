import base64
import json
import time
from typing import Dict, List, Tuple
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

from api_engine.models import (
    ApiDetectionResults,
    EndpointAnalysisBatch,
    EndpointDocumentation,
    HeadersRequest,
    MatchedRequest,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class HeaderOptimizer:
    """Finds minimal necessary headers for API endpoints."""

    def optimize(
        self,
        matched_requests: List[MatchedRequest],
        analyzed_endpoints: EndpointAnalysisBatch,
        output_file: str = None,
    ) -> Tuple[bool, ApiDetectionResults]:
        """
        Find the minimal set of headers required to make successful API requests.

        Args:
            matched_requests: List of matched requests objects
            analyzed_endpoints: List of endpoint analysis objects
            output_file: Optional path to save output results

        Returns:
            tuple: (success, api_detection_results)
        """
        try:
            logger.info(f"Finding minimal headers for {len(matched_requests)} requests")

            # Convert analyzed endpoints to a dictionary for easier lookup
            endpoint_descriptions = {
                endpoint.url: {
                    "explanation": endpoint.explanation,
                    "usefulness_score": endpoint.usefulness_score,
                }
                for endpoint in analyzed_endpoints.endpoints
            }

            logger.info(f"Finding minimal headers for {len(matched_requests)} requests")
            minimal_headers_data = self._find_minimal_headers(matched_requests)

            logger.info("Formatting output data")
            output_data = self._create_output_data(
                minimal_headers_data, endpoint_descriptions
            )

            # Optionally save results
            if output_file:
                logger.info(f"Saving results to {output_file}")
                self._save_output_data(output_data, output_file)

            logger.info("Header optimization completed")
            return True, output_data

        except Exception as e:
            logger.error(f"Header optimization failed: {str(e)}")
            return False, None

    def _load_matched_requests(self, file_path: str) -> List[Dict]:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_endpoint_descriptions(self, file_path: str) -> Dict[str, Dict]:
        endpoint_data = {}

        with open(file_path, "r", encoding="utf-8") as f:
            endpoints_data = json.load(f)
            for endpoint in endpoints_data:
                endpoint_data[endpoint["url"]] = {
                    "explanation": endpoint["explanation"],
                    "usefulness_score": endpoint["usefulness_score"],
                }

        return endpoint_data

    def _test_api_with_headers(
        self, api_endpoint: str, method: str, headers: Dict[str, str]
    ) -> Dict[str, str]:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()

            required_headers = {
                "accept": headers.get("accept", "*/*"),
                "user-agent": headers.get("user-agent", "Mozilla/5.0"),
            }

            valid_headers = {k: v for k, v in headers.items() if not k.startswith(":")}
            necessary_headers = valid_headers.copy()

            logger.info(f"Testing headers for {api_endpoint}")
            logger.info(f"Starting with {len(valid_headers)} headers")
            logger.info(f"Method: {method}")

            try:
                response = context.request.fetch(
                    api_endpoint,
                    method=method,
                    headers=valid_headers,
                    data="{}" if method.upper() in ["POST", "PUT", "PATCH"] else None,
                )
                initial_status = response.status
                try:
                    initial_body = response.text()
                except Exception:
                    initial_body = None
                logger.info(
                    f"Initial response - Status: {initial_status}, Body length: {len(initial_body) if initial_body else 0}"
                )
            except Exception as e:
                logger.error(f"Initial request failed: {e}")
                return valid_headers

            for header in list(necessary_headers.keys()):
                if header in required_headers:
                    logger.debug(f"Skipping required header: {header}")
                    continue

                try:
                    logger.debug(f"Testing without header: {header}")
                    test_headers = necessary_headers.copy()
                    test_headers.pop(header)

                    response = context.request.fetch(
                        api_endpoint,
                        method=method,
                        headers=test_headers,
                        data="{}"
                        if method.upper() in ["POST", "PUT", "PATCH"]
                        else None,
                    )

                    try:
                        current_body = response.text()
                    except Exception:
                        current_body = None

                    if (
                        response.status == initial_status
                        and current_body == initial_body
                    ):
                        logger.debug(f"Request succeeded without {header}, removing it")
                        necessary_headers.pop(header)
                    else:
                        logger.debug(
                            f"Request changed without {header} (status: {response.status}, body changed: {current_body != initial_body}), keeping it"
                        )

                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error testing without {header}: {e}")
                    continue

            browser.close()
            necessary_headers.update(required_headers)
            logger.info(f"Finished with {len(necessary_headers)} necessary headers")
            return necessary_headers

    def _find_minimal_headers(
        self, matched_requests: List[MatchedRequest]
    ) -> List[HeadersRequest]:
        necessary_headers = []

        for request in matched_requests:
            base_url = request.url
            method = request.method

            if ":path" in request.headers:
                path = request.headers[":path"]
                if "?" in path:
                    query_string = path.split("?", 1)[1]
                    url = f"{base_url}?{query_string}"
                else:
                    url = base_url
            else:
                url = base_url

            headers = {
                k: v for k, v in request.headers.items() if not k.startswith(":")
            }
            status_code = request.status_code

            logger.info(f"Processing API: {url}")
            logger.debug(f"Method: {method}, Original Status: {status_code}")

            if status_code in (200, 204):
                minimal_headers = self._test_api_with_headers(url, method, headers)

                if not any(
                    urlparse(entry.api_endpoint).scheme
                    + "://"
                    + urlparse(entry.api_endpoint).netloc
                    + urlparse(entry.api_endpoint).path
                    == base_url
                    and entry.method == method
                    for entry in necessary_headers
                ):
                    necessary_headers.append(
                        HeadersRequest(
                            api_endpoint=url,
                            method=method,
                            necessary_headers=minimal_headers,
                        )
                    )

        return necessary_headers

    def _format_endpoint_data(
        self,
        request: HeadersRequest,
        endpoint_data: Dict,
        all_requests: List[HeadersRequest],
    ) -> EndpointDocumentation:
        parsed_url = urlparse(request.api_endpoint)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        query_params = parse_qs(parsed_url.query)
        decoded_params = {}
        for k, v in query_params.items():
            try:
                if k == "d":
                    decoded = base64.b64decode(v[0]).decode("utf-8")
                    decoded_params[k] = json.loads(decoded)
                else:
                    decoded_params[k] = v[0]
            except Exception:
                decoded_params[k] = v[0]

        headers_str = " \\\n  ".join(
            [f"-H '{k}: {v}'" for k, v in request.necessary_headers.items()]
        )

        curl_cmd = f"curl '{request.api_endpoint}' \\\n  {headers_str}"

        endpoint_info = endpoint_data.get(
            base_url, {"explanation": "No description available", "usefulness_score": 0}
        )

        return EndpointDocumentation(
            url=base_url,
            description=endpoint_info["explanation"],
            usefulness_score=endpoint_info["usefulness_score"],
            method=request.method,
            required_headers=request.necessary_headers,
            example_params=decoded_params,
            curl_example=curl_cmd,
            notes="This endpoint accepts both GET and POST methods"
            if base_url in [r.api_endpoint for r in all_requests if r != request]
            else None,
        )

    def _create_output_data(
        self, minimal_headers_data: List[HeadersRequest], endpoint_descriptions: Dict
    ) -> ApiDetectionResults:
        output_data = {"endpoints": []}

        for request in minimal_headers_data:
            endpoint_data = self._format_endpoint_data(
                request, endpoint_descriptions, minimal_headers_data
            )
            output_data["endpoints"].append(endpoint_data.dict())

        return ApiDetectionResults(**output_data)

    def _save_output_data(
        self, output_data: ApiDetectionResults, output_file: str
    ) -> None:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data.dict(), f, indent=4)
