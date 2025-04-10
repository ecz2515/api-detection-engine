import json
from typing import Dict, List, Tuple

from openai import OpenAI

from api_engine.models import EndpointAnalysisBatch, FilteredEndpoint
from utils.logger import get_logger

logger = get_logger(__name__)


class EndpointAnalyzer:
    """Analyzes filtered API endpoints using OpenAI's LLM to determine value."""

    def __init__(self, api_key=None, model="gpt-4o-mini", chunk_size=5):
        """Initialize the analyzer.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
            chunk_size: Number of endpoints to analyze in a single API call
        """
        self.api_key = api_key
        self.model = model
        self.chunk_size = chunk_size
        self.client = None

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            logger.warning(
                "No API key provided. Will attempt to use environment variable."
            )
            self.client = OpenAI()

    def analyze(
        self, filtered_endpoints: List[FilteredEndpoint], output_file: str = None
    ) -> Tuple[bool, EndpointAnalysisBatch]:
        """Analyze endpoints and optionally save results to output file.

        Args:
            filtered_endpoints: List of FilteredEndpoint objects
            output_file: Optional path to save analysis results

        Returns:
            tuple: (success, list_of_endpoint_analyses)
        """
        try:
            logger.info(
                f"Starting endpoint analysis of {len(filtered_endpoints)} endpoints"
            )

            # Process data in chunks
            all_results = []
            endpoints_dict = {
                endpoint.url: endpoint.model_dump() for endpoint in filtered_endpoints
            }

            for chunk in self._chunk_data(endpoints_dict, self.chunk_size):
                result = self._analyze_endpoints(chunk)
                if hasattr(result, "endpoints"):
                    all_results.extend(result.endpoints)

            combined_results = EndpointAnalysisBatch(endpoints=all_results)

            # Optionally save results
            if output_file:
                with open(output_file, "w") as outfile:
                    json.dump(combined_results.model_dump(), outfile, indent=4)
                logger.info(f"Analysis results saved to {output_file}")

            logger.info(
                f"Analysis complete. Found {len(all_results)} valuable endpoints."
            )
            return True, combined_results

        except Exception as e:
            logger.error(f"Error during endpoint analysis: {str(e)}")
            return False, []

    def _chunk_data(self, data: Dict, chunk_size: int = 5):
        """Split data into smaller chunks for processing.

        Args:
            data: Dictionary of endpoint data
            chunk_size: Maximum number of endpoints per chunk

        Yields:
            Dict: Chunk of data
        """
        items = list(data.items())
        logger.info(f"Chunking {len(items)} endpoints into batches of {chunk_size}")
        for i in range(0, len(items), chunk_size):
            yield dict(items[i : i + chunk_size])

    def _analyze_endpoints(self, preprocessed_data: Dict) -> EndpointAnalysisBatch:
        """Process endpoints with the LLM.

        Args:
            preprocessed_data: Dictionary mapping URLs to request data

        Returns:
            List[EndpointAnalysis]: List of analyzed endpoints
        """
        try:
            formatted_endpoints_json = json.dumps(
                {"endpoints": preprocessed_data}, indent=2
            )

            # Create messages for LLM
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an API analysis assistant. Your task is to identify API endpoints that fetch valuable data. "
                        "These could include:\n"
                        "- User data and metadata\n"
                        "- Analytics and tracking\n"
                        "- Search and recommendation results\n"
                        "- Logs, system events, or behavioral data\n\n"
                        "Please analyze the provided endpoints and determine which ones are likely to contain valuable data. "
                        "For each endpoint you identify:\n"
                        "1. Provide a clear explanation of why it's valuable\n"
                        "2. Assign a usefulness score from 0-100 where:\n"
                        "   - 0-20: Minimal value, mostly static or basic data\n"
                        "   - 21-40: Some value but limited utility\n"
                        "   - 41-60: Moderately useful data\n"
                        "   - 61-80: High-value data with clear utility\n"
                        "   - 81-100: Critical data with significant strategic value\n\n"
                        "If no endpoints are found valuable, include at least one as a potential candidate with a reason why it might be useful "
                        "and a corresponding score.\n\n"
                        "Format the response strictly as a JSON object with an 'endpoints' array containing URL(s), explanations, and usefulness scores."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Here is a batch of API endpoints to analyze:\n\n{formatted_endpoints_json}",
                },
            ]

            logger.info(f"Making API request with model {self.model}...")
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                max_tokens=1500,
                temperature=0.1,
                response_format=EndpointAnalysisBatch,
            )

            logger.info("API request successful.")

            return response.choices[0].message.parsed

        except Exception as e:
            logger.error(f"Error during API processing: {str(e)}")
            return []
