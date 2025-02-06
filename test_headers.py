import json
import time
import requests

def test_minimal_headers():
    # Load the necessary headers from the JSON file
    with open('necessary_headers.json', 'r') as f:
        header_data = json.load(f)

    print("Testing all endpoints...")
    failed_tests = []

    # Test each endpoint with its minimal headers
    for entry in header_data['endpoints']:
        base_url = entry['url']
        method = entry['method']
        headers = entry['required_headers']
        
        # Add query parameters if they exist
        if entry['example_params']:
            params = entry['example_params']
            url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        else:
            url = base_url

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                data = "{}" if "content-type" in headers and "json" in headers["content-type"].lower() else None
                response = requests.post(url, headers=headers, data=data, timeout=10)
            
            if response.status_code in (200, 204):
                print(f"✓ {method} {base_url} - {response.status_code}")
            else:
                print(f"✗ {method} {base_url} - {response.status_code}")
                failed_tests.append((base_url, method, response.status_code))
                
        except Exception as e:
            print(f"✗ {method} {base_url} - Error: {str(e)}")
            failed_tests.append((base_url, method, str(e)))

    if failed_tests:
        print("\nFailed tests:")
        for url, method, status in failed_tests:
            print(f"{method} {url} - {status}")
    else:
        print("\nAll tests passed!")

if __name__ == "__main__":
    test_minimal_headers()
