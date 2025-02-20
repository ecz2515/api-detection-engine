import json
import re

def load_har_file(har_file):
    with open(har_file, "r", encoding="utf-8") as f:
        har_data = json.load(f)

    requests = []
    for entry in har_data["log"]["entries"]:
        request = entry["request"]
        response = entry["response"]

        requests.append({
            "url": request["url"].split("?")[0],
            "method": request["method"],
            "headers": {h["name"]: h["value"] for h in request["headers"]},
            "status_code": response["status"],
        })

    return requests

def extract_valuable_endpoints(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        endpoints_data = json.load(f)
        valuable_endpoints = [endpoint["url"] for endpoint in endpoints_data]
        return valuable_endpoints

def match_endpoints(har_requests, valuable_endpoints):
    matched_requests = []
    
    for request in har_requests:
        for endpoint in valuable_endpoints:
            if request["url"].startswith(endpoint):
                matched_requests.append(request)
                break

    return matched_requests

if __name__ == "__main__":
    har_file = "test_files/www.amazon.com.har"
    endpoints_file = "analyzed_endpoints.json"

    har_requests = load_har_file(har_file)
    print(f"Loaded {len(har_requests)} requests from HAR file")
    
    valuable_endpoints = extract_valuable_endpoints(endpoints_file)
    print(f"Found {len(valuable_endpoints)} valuable endpoints to match")

    matched_requests = match_endpoints(har_requests, valuable_endpoints)

    with open("matched_requests.json", "w") as f:
        json.dump(matched_requests, f, indent=4)

    print(f"Matched {len(matched_requests)} requests saved to matched_requests.json")
