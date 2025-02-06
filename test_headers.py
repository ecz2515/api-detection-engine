import json
import time
import requests
import subprocess

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
        
        try:
            # Execute the curl command directly, without text=True to handle binary responses
            result = subprocess.run(
                entry['curl_example'],
                shell=True,
                capture_output=True
            )
            
            # Check if curl command was successful (curl exit code 0)
            if result.returncode == 0:
                print(f"✓ {method} {base_url} - Success")
            else:
                print(f"✗ {method} {base_url} - Failed")
                # Try to decode error message if possible
                try:
                    error = result.stderr.decode('utf-8')
                except:
                    error = str(result.stderr)
                print(f"   Error: {error}")
                failed_tests.append((base_url, method, "Curl command failed"))
                
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
