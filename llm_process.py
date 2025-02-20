import json
import time
import logging
import os
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)

class EndpointAnalysis(BaseModel):
    url: str
    explanation: str

def analyze_endpoints_with_llm(preprocessed_data):
    try:
        logging.info("Processing %d endpoints...", len(preprocessed_data))

        formatted_endpoints = [
            {
                "url": url,
                "methods": list(set(req["method"] for req in requests)),
                "params": requests[0].get("query_params", {}),
                "sample_headers": requests[0].get("headers", {}),
                "sample_post_data": requests[0].get("post_data", None),
            }
            for url, requests in preprocessed_data.items()
        ]

        logging.info("Formatted endpoints successfully.")

        formatted_endpoints_json = json.dumps({"endpoints": formatted_endpoints}, indent=2)

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
                    "Provide a clear explanation for each endpoint you identify as valuable. If no endpoints are found valuable, "
                    "include at least one as a potential candidate with a reason why it might be useful.\n\n"
                    "Format the response strictly as a JSON object with an 'endpoints' array containing URL(s) and explanations."
                )
            },
            {
                "role": "user",
                "content": f"Here is a batch of API endpoints to analyze:\n\n{formatted_endpoints_json}"
            },
        ]

        logging.info("Making API request with structured outputs...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1500,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        logging.info("API request successful.")

        try:
            response_content = response.choices[0].message.content
            parsed_data = json.loads(response_content)

            endpoints = [EndpointAnalysis(**ep) for ep in parsed_data.get("endpoints", [])]
            logging.info("Extracted %d valuable endpoints.", len(endpoints))
            return endpoints

        except (ValidationError, json.JSONDecodeError) as e:
            logging.error("Error parsing API response: %s", str(e))
            return []

    except Exception as e:
        logging.error("Error during API processing: %s", str(e))
        return []

def chunk_data(data, chunk_size=5):
    items = list(data.items())
    logging.info("Total endpoints before chunking: %d", len(items))
    for i in range(0, len(items), chunk_size):
        yield dict(items[i:i + chunk_size])

if __name__ == "__main__":
    logging.info("Starting endpoint analysis process")

    try:
        with open("preprocessed_requests.json", "r") as infile:
            preprocessed_data = json.load(infile)
            logging.info("Loaded %d endpoints for analysis.", len(preprocessed_data))
    except Exception as e:
        logging.error("Error loading preprocessed data: %s", str(e))
        exit(1)

    open("analyzed_endpoints.json", "w").close()

    all_results = []
    for chunk in chunk_data(preprocessed_data, chunk_size=5):
        result = analyze_endpoints_with_llm(chunk)
        if isinstance(result, list):
            all_results.extend(result)

    with open("analyzed_endpoints.json", "w") as outfile:
        json.dump([ep.dict() for ep in all_results], outfile, indent=4)

    logging.info("Analysis complete. Results saved to 'analyzed_endpoints.json'.")
