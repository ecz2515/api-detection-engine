import os
import time

from api_engine.analyzer import EndpointAnalyzer
from api_engine.capture import HarCapture
from api_engine.filter import HarFilter
from api_engine.headers import HeaderOptimizer
from api_engine.matcher import HarMatcher
from utils.logger import get_logger

# Set up logger
logger = get_logger(__name__)


class ApiDetectionPipeline:
    """Orchestrates the entire API detection pipeline."""

    def __init__(
        self, output_dir="data", openai_api_key=None, openai_model="gpt-4o-mini"
    ):
        """Initialize the pipeline.

        Args:
            output_dir: Directory to store output files
            openai_api_key: OpenAI API key for endpoint analysis
            openai_model: OpenAI model to use for analysis
        """
        self.output_dir = output_dir
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Initialize component instances
        self.har_capture = HarCapture()
        self.har_filter = HarFilter()
        self.endpoint_analyzer = EndpointAnalyzer(
            api_key=openai_api_key, model=openai_model
        )
        self.har_matcher = HarMatcher()
        self.header_optimizer = HeaderOptimizer()

        # File paths for intermediate outputs
        self.har_file = os.path.join(output_dir, "network_traffic.har")
        self.filtered_file = os.path.join(output_dir, "filtered_requests.json")
        self.analyzed_file = os.path.join(output_dir, "analyzed_endpoints.json")
        self.matched_file = os.path.join(output_dir, "matched_requests.json")
        self.headers_file = os.path.join(output_dir, "necessary_headers.json")

    def run(self, url, request_type="GET"):
        """Run the complete pipeline.

        Args:
            url: The URL to analyze
            request_type: HTTP method to filter (GET, POST, etc.)

        Returns:
            tuple: (success, output_file_path)
        """
        start_time = time.time()
        logger.info(
            f"Starting API detection pipeline for {url} with {request_type} requests"
        )

        try:
            # Step 1: Capture HAR
            logger.info("Step 1: Capturing HAR traffic")
            if not self.har_capture.capture(url, self.har_file):
                logger.error("HAR capture failed")
                return False, None

            # Step 2: Filter HAR requests
            logger.info("Step 2: Filtering HAR requests")
            if not self.har_filter.filter(
                self.har_file, request_type, self.filtered_file
            ):
                logger.error("HAR filtering failed")
                return False, None

            # Step 3: Analyze endpoints with LLM
            logger.info("Step 3: Analyzing endpoints with LLM")
            if not self.endpoint_analyzer.analyze(
                self.filtered_file, self.analyzed_file
            ):
                logger.error("Endpoint analysis failed")
                return False, None

            # Step 4: Match HAR requests with valuable endpoints
            logger.info("Step 4: Matching HAR requests with valuable endpoints")
            if not self.har_matcher.match(
                self.har_file, self.analyzed_file, self.matched_file
            ):
                logger.error("Request matching failed")
                return False, None

            # Step 5: Find necessary headers
            logger.info("Step 5: Finding necessary headers")
            if not self.header_optimizer.optimize(
                self.matched_file, self.analyzed_file, self.headers_file
            ):
                logger.error("Header optimization failed")
                return False, None

            elapsed_time = time.time() - start_time
            logger.info(
                f"Pipeline completed successfully in {elapsed_time:.2f} seconds"
            )
            return True, self.headers_file

        except Exception as e:
            logger.exception(f"Pipeline execution failed: {str(e)}")
            return False, None
