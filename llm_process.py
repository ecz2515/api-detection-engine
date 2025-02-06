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
        prompt = """
        Below is a list of API endpoints and their details. Identify the endpoints that are likely to fetch valuable data (e.g., user metadata, search suggestions, category details). Output each valuable endpoint in the following format:
        
        URL: <endpoint URL>
        Explanation: <why this endpoint is valuable>

        Example:
        URL: https://api.example.com/user
        Explanation: This endpoint fetches user metadata, which is valuable for understanding user behavior and preferences.

        Add a blank line between each URL-Explanation pair.

        Do not include any additional text outside this format.

        Input:
        {}
        """.format(json.dumps(preprocessed_data, indent=4))

        # Use the chat/completions endpoint with chat models
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use a chat model
            messages=[
                {"role": "system", "content": "You are an API analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.5
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"


def chunk_data(data, chunk_size=5):
    # Break data into smaller chunks
    items = list(data.items())
    for i in range(0, len(items), chunk_size):
        yield dict(items[i:i + chunk_size])

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
    open('analyzed_endpoints.txt', 'w').close()

    # Analyze each chunk
    chunk_count = 0
    for chunk in chunk_data(preprocessed_data, chunk_size=5):
        chunk_count += 1
        logging.info(f"Processing chunk {chunk_count}")
        result = analyze_endpoints_with_llm(chunk)
        with open("analyzed_endpoints.txt", "a") as outfile:
            outfile.write(result + "\n")
        # logging.info(f"Completed chunk {chunk_count}. Waiting before next request...")
        # time.sleep(1)  # Delay between requests

    logging.info("Analysis complete. Results saved to 'analyzed_endpoints.txt'.")
