import json
import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import requests
import base64

class HeadersRequest(BaseModel):
    """Request model containing API endpoint, method and headers"""
    api_endpoint: str = Field(..., description="API endpoint URL")
    method: str = Field(..., description="HTTP method (GET, POST etc)")
    necessary_headers: Dict[str, str] = Field(..., description="Minimal required headers")

class HeadersResponse(BaseModel):
    """Response model containing list of validated header requests"""
    requests: List[HeadersRequest]

def load_matched_requests(file_path: str) -> List[Dict]:
    """Load and parse matched requests from JSON file"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_endpoint_descriptions(file_path: str) -> Dict[str, str]:
    """Load endpoint descriptions from analyzed_endpoints.txt"""
    descriptions = {}
    current_url = None
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('URL: '):
                current_url = line.replace('URL: ', '').strip()
            elif line.startswith('Explanation: ') and current_url:
                description = line.replace('Explanation: ', '').strip()
                descriptions[current_url] = description
                current_url = None
    
    return descriptions

def test_api_with_headers(api_endpoint: str, method: str, headers: Dict[str, str]) -> Dict[str, str]:
    """
    Test API endpoint by removing headers one by one to find minimal set
    Returns dict of necessary headers
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()

        # Always required headers
        required_headers = {
            "accept": headers.get("accept", "*/*"),
            "user-agent": headers.get("user-agent", "Mozilla/5.0"),
        }
        
        # Remove colon-prefixed headers and add required ones
        valid_headers = {k: v for k, v in headers.items() if not k.startswith(":")}
        necessary_headers = valid_headers.copy()

        print(f"\nTesting headers for {api_endpoint}")
        print(f"Starting with {len(valid_headers)} headers")
        print(f"Method: {method}")

        # Store initial response for comparison
        try:
            response = context.request.fetch(
                api_endpoint,
                method=method,
                headers=valid_headers,
                data="{}" if method.upper() in ['POST', 'PUT', 'PATCH'] else None
            )
            initial_status = response.status
            try:
                initial_body = response.text()
            except:
                initial_body = None
            print(f"Initial response - Status: {initial_status}, Body length: {len(initial_body) if initial_body else 0}")
        except Exception as e:
            print(f"Initial request failed: {e}")
            return valid_headers

        # Test removing each header individually (except required ones)
        for header in list(necessary_headers.keys()):
            if header in required_headers:
                print(f"Skipping required header: {header}")
                continue
                
            try:
                print(f"Testing without header: {header}")
                test_headers = necessary_headers.copy()
                test_headers.pop(header)
                
                response = context.request.fetch(
                    api_endpoint,
                    method=method,
                    headers=test_headers,
                    data="{}" if method.upper() in ['POST', 'PUT', 'PATCH'] else None
                )
                
                # Compare both status code and response body
                try:
                    current_body = response.text()
                except:
                    current_body = None
                
                if response.status == initial_status and current_body == initial_body:
                    print(f"Request succeeded without {header}, removing it")
                    necessary_headers.pop(header)
                else:
                    print(f"Request changed without {header} (status: {response.status}, body changed: {current_body != initial_body}), keeping it")

                time.sleep(1)  # Delay between tests

            except Exception as e:
                print(f"Error testing without {header}: {e}")
                continue

        browser.close()
        # Add back required headers
        necessary_headers.update(required_headers)
        print(f"Finished with {len(necessary_headers)} necessary headers")
        return necessary_headers

def find_minimal_headers(matched_requests: List[Dict]) -> List[Dict]:
    """Find necessary headers for each unique API endpoint"""
    necessary_headers = []
    
    for request in matched_requests:
        base_url = request["url"]
        method = request["method"]
        
        # Extract query parameters from :path if present
        if ":path" in request["headers"]:
            path = request["headers"][":path"]
            if "?" in path:
                # Get everything after the ? from the path
                query_string = path.split("?", 1)[1]
                url = f"{base_url}?{query_string}"
            else:
                url = base_url
        else:
            url = base_url

        headers = {k: v for k, v in request["headers"].items() 
                  if not k.startswith(":")}  # Remove HTTP/2 pseudo-headers
        status_code = request["status_code"]

        print(f"\nProcessing API: {url}")
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        print(f"Query parameters: {query_params}")
        print(f"Method: {method}, Original Status: {status_code}")

        if status_code in (200, 204):
            minimal_headers = test_api_with_headers(url, method, headers)
            
            # Only add if this endpoint+method combination isn't already present
            if not any(urlparse(entry["api_endpoint"]).scheme + "://" + 
                      urlparse(entry["api_endpoint"]).netloc + 
                      urlparse(entry["api_endpoint"]).path == base_url 
                      and entry["method"] == method for entry in necessary_headers):
                necessary_headers.append({
                    "api_endpoint": url,  # Store complete URL with query params
                    "method": method,
                    "necessary_headers": minimal_headers
                })

    # Validate data with Pydantic
    response = HeadersResponse(requests=necessary_headers)
    return response.requests

def test_minimal_headers():
    # Load the necessary headers from the JSON file
    with open('necessary_headers.json', 'r') as f:
        header_data = json.load(f)

    # Test each endpoint with its minimal headers
    for entry in header_data:
        url = entry['api_endpoint']  # This now includes query parameters
        method = entry['method']
        headers = entry['necessary_headers']

        print(f"\nTesting {method} {url}")
        print(f"Using {len(headers)} headers")

        try:
            # Add retry logic with delay
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    if method == 'GET':
                        response = requests.get(url, headers=headers, timeout=10)
                    elif method == 'POST':
                        # Add empty JSON body for POST requests if needed
                        data = "{}" if "content-type" in headers and "json" in headers["content-type"].lower() else None
                        response = requests.post(url, headers=headers, data=data, timeout=10)
                    else:
                        print(f"Unsupported method: {method}")
                        continue

                    print(f"Status code: {response.status_code}")
                    if response.status_code >= 400:
                        print(f"Response body: {response.text[:200]}...")
                    
                    assert response.status_code in (200, 204), f"Expected 200 or 204, got {response.status_code}"
                    print("✓ Test passed")
                    break  # Success, exit retry loop
                    
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:  # Don't sleep on last attempt
                        print(f"Attempt {attempt + 1} failed: {str(e)}")
                        time.sleep(retry_delay)
                    else:
                        raise  # Re-raise the last exception if all retries failed

        except Exception as e:
            print(f"✗ Test failed: {str(e)}")

def format_endpoint_data(request, endpoint_descriptions):
    parsed_url = urlparse(request.api_endpoint)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    # Parse and decode query parameters
    query_params = parse_qs(parsed_url.query)
    decoded_params = {}
    for k, v in query_params.items():
        try:
            # Try to decode base64 parameters
            if k == 'd':
                decoded = base64.b64decode(v[0]).decode('utf-8')
                decoded_params[k] = json.loads(decoded)
            else:
                decoded_params[k] = v[0]
        except:
            decoded_params[k] = v[0]
    
    # Create a more readable curl example
    headers_str = ' \\\n  '.join([f"-H '{k}: {v}'" for k, v in request.necessary_headers.items()])
    # Shorten URL in curl example if it's too long
    example_url = request.api_endpoint
    if len(example_url) > 100:
        example_url = f"{base_url}?...  # Query parameters omitted for brevity"
    
    curl_cmd = f"curl '{example_url}' \\\n  {headers_str}"
    
    return {
        "url": base_url,
        "description": endpoint_descriptions.get(base_url, "No description available"),
        "method": request.method,
        "required_headers": request.necessary_headers,
        "example_params": decoded_params,
        "curl_example": curl_cmd,
        "notes": "This endpoint accepts both GET and POST methods" if base_url in [r.api_endpoint for r in minimal_headers_data if r != request] else None
    }

if __name__ == "__main__":
    matched_requests_file = "matched_requests.json"
    analyzed_endpoints_file = "analyzed_endpoints.txt"
    output_file = "necessary_headers.json"
    
    print(f"Loading requests from {matched_requests_file}")
    matched_requests = load_matched_requests(matched_requests_file)
    
    print(f"Loading endpoint descriptions from {analyzed_endpoints_file}")
    endpoint_descriptions = load_endpoint_descriptions(analyzed_endpoints_file)
    
    print(f"Finding minimal headers for {len(matched_requests)} requests")
    minimal_headers_data = find_minimal_headers(matched_requests)
    
    print(f"\nSaving results to {output_file}")
    
    # Convert to new format with descriptions
    output_data = {
        "endpoints": []
    }
    
    for request in minimal_headers_data:
        endpoint_data = format_endpoint_data(request, endpoint_descriptions)
        output_data["endpoints"].append(endpoint_data)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
    
    print(f"Minimal necessary headers saved to {output_file}")
