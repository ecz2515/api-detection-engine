#!/bin/bash
# build.sh: Execute the full pipeline for capturing and processing HAR logs.
# Usage: ./build.sh <URL> <REQUEST_TYPE>
# The script assumes that each Python script produces its expected output file.

set -e  # Exit immediately if any command fails

# Check for URL and REQUEST_TYPE arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <URL> <REQUEST_TYPE>"
    exit 1
fi

URL="$1"
REQUEST_TYPE="$2"

echo "Starting pipeline for URL: $URL with request type: $REQUEST_TYPE"

echo "Step 1: Capturing HAR logs..."
python3 capture_har.py "$URL"
echo "HAR capture complete. (Output: network_traffic.har)"

echo "Step 2: Filtering HAR logs..."
python3 har_filter_requests.py "network_traffic.har" "$REQUEST_TYPE"
echo "Filtering complete. (Output: filtered_requests.json)"

echo "Step 3: Processing filtered HAR logs with the LLM..."
python3 llm_process.py
echo "LLM processing complete. (Output: preprocessed_requests.json or analyzed_endpoints.json)"

echo "Step 4: Matching processed HAR requests..."
python3 match_har_requests.py "network_traffic.har"
echo "Matching complete. (Output: matched_requests.json)"

echo "Step 5: Extracting necessary headers..."
python3 find_necessary_headers.py
echo "Header extraction complete. (Output: necessary_headers.json)"

echo "Build pipeline complete."
