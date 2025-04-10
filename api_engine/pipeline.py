import os
import time
from typing import Dict, Optional, Tuple

from api_engine.analyzer import EndpointAnalyzer
from api_engine.capture import HarCapture
from api_engine.filter import HarFilter
from api_engine.headers import HeaderOptimizer
from api_engine.matcher import HarMatcher
from api_engine.models import ApiDetectionResults
from utils.logger import get_logger

# Set up logger
logger = get_logger(__name__)


class ApiDetectionPipeline:
    """Orchestrates the entire API detection pipeline."""

    def __init__(
        self, output_dir=None, openai_api_key=None, openai_model="gpt-4o-mini"
    ):
        """Initialize the pipeline.

        Args:
            output_dir: Optional directory to store output files
            openai_api_key: OpenAI API key for endpoint analysis
            openai_model: OpenAI model to use for analysis
        """
        self.output_dir = output_dir
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model

        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Initialize component instances
        self.har_capture = HarCapture()
        self.har_filter = HarFilter()
        self.endpoint_analyzer = EndpointAnalyzer(
            api_key=openai_api_key, model=openai_model
        )
        self.har_matcher = HarMatcher()
        self.header_optimizer = HeaderOptimizer()

        # Define file paths for output if directory is specified
        if output_dir:
            self.har_file = os.path.join(output_dir, "network_traffic.har")
            self.filtered_file = os.path.join(output_dir, "filtered_requests.json")
            self.analyzed_file = os.path.join(output_dir, "analyzed_endpoints.json")
            self.matched_file = os.path.join(output_dir, "matched_requests.json")
            self.headers_file = os.path.join(output_dir, "necessary_headers.json")
        else:
            self.har_file = self.filtered_file = self.analyzed_file = (
                self.matched_file
            ) = self.headers_file = None

    def run(
        self, url, request_type="GET"
    ) -> Tuple[bool, Optional[ApiDetectionResults], Dict]:
        """Run the complete pipeline.

        Args:
            url: The URL to analyze
            request_type: HTTP method to filter (GET, POST, etc.)

        Returns:
            tuple: (success, api_detection_results, intermediate_data)
        """
        start_time = time.time()
        logger.info(
            f"Starting API detection pipeline for {url} with {request_type} requests"
        )

        # Store intermediate results
        intermediate_data = {}

        try:
            # Step 1: Capture HAR
            logger.info("Step 1: Capturing HAR traffic")
            capture_success, har_data = self.har_capture.capture(url, self.har_file)
            if not capture_success:
                logger.error("HAR capture failed")
                return False, None, intermediate_data

            intermediate_data["har_data"] = har_data

            # Step 2: Filter HAR requests
            logger.info("Step 2: Filtering HAR requests")
            filter_success, filtered_endpoints = self.har_filter.filter(
                har_data, request_type, self.filtered_file
            )
            if not filter_success:
                logger.error("HAR filtering failed")
                return False, None, intermediate_data

            intermediate_data["filtered_endpoints"] = filtered_endpoints

            # Step 3: Analyze endpoints with LLM
            logger.info("Step 3: Analyzing endpoints with LLM")
            analysis_success, analyzed_endpoints = self.endpoint_analyzer.analyze(
                filtered_endpoints, self.analyzed_file
            )
            if not analysis_success:
                logger.error("Endpoint analysis failed")
                return False, None, intermediate_data

            intermediate_data["analyzed_endpoints"] = analyzed_endpoints

            # Step 4: Match HAR requests with valuable endpoints
            logger.info("Step 4: Matching HAR requests with valuable endpoints")
            match_success, matched_requests = self.har_matcher.match(
                har_data, analyzed_endpoints, self.matched_file
            )
            if not match_success:
                logger.error("Request matching failed")
                return False, None, intermediate_data

            intermediate_data["matched_requests"] = matched_requests

            # Step 5: Find necessary headers
            logger.info("Step 5: Finding necessary headers")
            optimize_success, api_results = self.header_optimizer.optimize(
                matched_requests, analyzed_endpoints, self.headers_file
            )
            if not optimize_success:
                logger.error("Header optimization failed")
                return False, None, intermediate_data

            elapsed_time = time.time() - start_time
            logger.info(
                f"Pipeline completed successfully in {elapsed_time:.2f} seconds"
            )
            return True, api_results, intermediate_data

        except Exception as e:
            logger.exception(f"Pipeline execution failed: {str(e)}")
            return False, None, intermediate_data
