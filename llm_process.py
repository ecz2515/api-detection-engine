import json
import time
import logging
import os
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()  # Load environment variables from .env file
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_endpoints_with_llm(preprocessed_data):
    try:
        # Debug: Log the input data
        logging.info("Input data type: %s", type(preprocessed_data))
        logging.info("Input data keys: %s", list(preprocessed_data.keys()))

        # Format the endpoints data into a more digestible format for the LLM
        formatted_endpoints = []
        try:
            for url, requests in preprocessed_data.items():
                endpoint_info = {
                    "url": url,
                    "methods": list(set(req["method"] for req in requests)),
                    "params": requests[0].get("query_params", {}),
                    "sample_headers": requests[0].get("headers", {}),
                    "sample_post_data": requests[0].get("post_data", None)
                }
                formatted_endpoints.append(endpoint_info)
                logging.info("Successfully formatted endpoint: %s", url)
        except Exception as e:
            logging.error("Error formatting endpoints: %s", str(e))
            logging.error("Error occurred while processing URL: %s", url if 'url' in locals() else 'unknown')
            raise

        # Debug: Log the formatted endpoints
        logging.info("Number of formatted endpoints: %d", len(formatted_endpoints))
        logging.info("First formatted endpoint: %s", json.dumps(formatted_endpoints[0]) if formatted_endpoints else "None")

        try:
            logging.info("Starting prompt formatting...")
            
            # Log the formatted_endpoints before JSON conversion
            logging.info("formatted_endpoints type: %s", type(formatted_endpoints))
            
            # Try JSON conversion separately
            endpoints_json = json.dumps(formatted_endpoints, indent=2)
            logging.info("JSON conversion successful")
            
            # Create prompt parts separately
            base_prompt = (
                "Below is a list of API endpoints and their details. Analyze each endpoint and identify those that might "
                "fetch valuable data (e.g., user metadata, search suggestions, analytics, tracking, user interactions, "
                "or any other potentially interesting data). Consider endpoints that handle:\n"
                "- User data and behavior\n"
                "- Analytics and metrics\n"
                "- System events and logs\n"
                "- Content and metadata\n"
                "- Search and recommendations\n\n"
                "Output each valuable endpoint in the following format:\n\n"
                "{\n"
                "    \"endpoints\": [\n"
                "        {\n"
                "            \"url\": \"https://api.example.com/user\",\n"
                "            \"explanation\": \"This endpoint fetches user metadata\"\n"
                "        }\n"
                "    ]\n"
                "}\n\n"
                "Input endpoints:\n"
            )
            
            logging.info("Base prompt created")
            
            # Combine parts
            prompt_text = base_prompt + endpoints_json
            
            logging.info("Prompt creation successful")
            logging.info("Prompt length: %d", len(prompt_text))

            # Debug: Log the formatted prompt
            logging.info("Formatted prompt preview: %s", prompt_text[:500] + "...")

            # Prepare API call parameters
            messages = [
                {
                    "role": "system", 
                    "content": "You are an API analysis assistant. Thoroughly analyze each endpoint and identify all "
                              "endpoints that might contain valuable data. Be comprehensive in your analysis and include "
                              "any endpoint that could provide insights into user behavior, system operations, or valuable metadata. "
                              "Always respond with a JSON object containing an 'endpoints' array."
                },
                {
                    "role": "user", 
                    "content": prompt_text
                }
            ]
            
            logging.info("Preparing API call...")
            logging.info("Messages structure: %s", json.dumps([{"role": m["role"]} for m in messages]))
            
            # Make the API call
            logging.info("Making API request to OpenAI...")
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an API analysis assistant. Thoroughly analyze each endpoint and identify all "
                                      "endpoints that might contain valuable data. Be comprehensive in your analysis and include "
                                      "any endpoint that could provide insights into user behavior, system operations, or valuable metadata. "
                                      "Always respond with a JSON object containing an 'endpoints' array."
                        },
                        {
                            "role": "user", 
                            "content": prompt_text
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.5,
                    response_format={ "type": "json_object" }
                )
                logging.info("API request successful")
            except Exception as api_error:
                logging.error("API request failed: %s", str(api_error))
                raise

            logging.info("Processing API response...")
            logging.info("Response type: %s", type(response))
            
            # Process the response
            if not hasattr(response, 'choices'):
                logging.error("Response has no choices attribute")
                return []
                
            if not response.choices:
                logging.error("Response choices is empty")
                return []
                
            if not hasattr(response.choices[0], 'message'):
                logging.error("First choice has no message attribute")
                return []
                
            if not hasattr(response.choices[0].message, 'content'):
                logging.error("Message has no content attribute")
                return []
                
            content = response.choices[0].message.content
            logging.info("Response content: %s", content)
            
            try:
                parsed_response = json.loads(content)
                logging.info("Parsed response: %s", json.dumps(parsed_response))
                
                if isinstance(parsed_response, dict) and "endpoints" in parsed_response:
                    endpoints = parsed_response["endpoints"]
                    logging.info("Successfully extracted endpoints: %s", json.dumps(endpoints))
                    return endpoints
                else:
                    logging.error("Invalid response format: %s", parsed_response)
                    return []
                    
            except json.JSONDecodeError as e:
                logging.error("Failed to parse response as JSON: %s", e)
                logging.error("Raw content that failed to parse: %s", content)
                return []

        except Exception as e:
            logging.error("API call error: %s", str(e))
            logging.error("Error type: %s", type(e).__name__)
            logging.error("Full error details: %s", repr(e))
            return []

    except Exception as e:
        logging.error("Top level error: %s", str(e))
        logging.error("Error type: %s", type(e).__name__)
        logging.error("Full error details: %s", repr(e))
        return []


def chunk_data(data, chunk_size=5):
    # Break data into smaller chunks
    items = list(data.items())
    logging.info("Total items before chunking: %d", len(items))
    for i in range(0, len(items), chunk_size):
        chunk = dict(items[i:i + chunk_size])
        logging.info("Created chunk with %d items", len(chunk))
        logging.info("Chunk keys: %s", list(chunk.keys()))
        yield chunk

if __name__ == "__main__":
    logging.info("Starting endpoint analysis process")
    
    # Load preprocessed data
    try:
        with open("preprocessed_requests.json", "r") as infile:
            preprocessed_data = json.load(infile)
            logging.info(f"Successfully loaded {len(preprocessed_data)} endpoints for analysis")
    except Exception as e:
        logging.error(f"Error loading preprocessed data: {e}")
        exit(1)

    # Create/clear the output file
    open('analyzed_endpoints.json', 'w').close()

    # Analyze each chunk
    chunk_count = 0
    all_results = []
    for chunk in chunk_data(preprocessed_data, chunk_size=5):
        chunk_count += 1
        logging.info(f"Processing chunk {chunk_count}")
        result = analyze_endpoints_with_llm(chunk)
        if isinstance(result, list):
            all_results.extend(result)
        else:
            logging.error(f"Error in processing chunk {chunk_count}: {result}")

    # Save all results to a JSON file
    with open("analyzed_endpoints.json", "w") as outfile:
        json.dump(all_results, outfile, indent=4)

    logging.info("Analysis complete. Results saved to 'analyzed_endpoints.json'.")
