import json
import sys
from collections import defaultdict


def filter_and_preprocess_har(har_file_path, request_type):
    with open(har_file_path, "r") as file:
        har_data = json.load(file)

    entries = har_data["log"]["entries"]
    grouped_requests = defaultdict(list)

    for entry in entries:
        request = entry["request"]
        if request["method"] == request_type:
            endpoint = request["url"].split("?")[0]

            query_params = {}
            for param in request.get("queryString", []):
                query_params[param["name"]] = param["value"]

            headers = {}
            for header in request.get("headers", []):
                headers[header["name"]] = header["value"]

            filtered_headers = {}
            for k in headers:
                if k.lower() in ["authorization", "content-type"]:
                    filtered_headers[k] = headers[k]

            grouped_requests[endpoint].append(
                {
                    "method": request["method"],
                    "query_params": query_params,
                    "headers": filtered_headers,
                    "post_data": request.get("postData", {}).get("text", None),
                }
            )

    return dict(grouped_requests)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python har_filter_requests.py <HAR_FILE_PATH> <REQUEST_TYPE>")
        sys.exit(1)

    har_file_path = sys.argv[1]
    request_type = sys.argv[2]

    preprocessed_data = filter_and_preprocess_har(har_file_path, request_type)

    with open("preprocessed_requests.json", "w") as outfile:
        json.dump(preprocessed_data, outfile, indent=4)

    print("Preprocessed data saved to preprocessed_requests.json")
