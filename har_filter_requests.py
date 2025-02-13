import json
from collections import defaultdict

def filter_and_preprocess_har(har_file_path, request_type):
    """
    Filters requests in a .har file by the specified request type and preprocesses
    them to group API calls by endpoint.

    :param har_file_path: Path to the .har file
    :param request_type: HTTP method to filter by (e.g., "GET", "POST")
    :return: Preprocessed data grouped by endpoint
    """

    with open(har_file_path, 'r') as file:
        har_data = json.load(file)

    entries = har_data['log']['entries']
    grouped_requests = defaultdict(list)

    for entry in entries:
        request = entry['request']
        if request['method'] == request_type:
            # Extract endpoint by removing query parameters from the URL
            endpoint = request['url'].split('?')[0]
            
            # Convert query params list to dict
            query_params = {}
            for param in request.get('queryString', []):
                query_params[param['name']] = param['value']
            
            # Convert headers list to dict
            headers = {}
            for header in request.get('headers', []):
                headers[header['name']] = header['value']
            
            # Filter headers
            filtered_headers = {}
            for k in headers:
                if k.lower() in ['authorization', 'content-type']:
                    filtered_headers[k] = headers[k]

            # Group and append request data
            grouped_requests[endpoint].append({
                "method": request['method'],
                "query_params": query_params,
                "headers": filtered_headers,
                "post_data": request.get('postData', {}).get('text', None)
            })

    return dict(grouped_requests)

if __name__ == "__main__":
    # Path to .har file
    har_file_path = "test_files/www.amazon.com.har"
    request_type = "GET"
    
    # Filter and preprocess .har file
    preprocessed_data = filter_and_preprocess_har(har_file_path, request_type)
    
    # Print grouped requests
    # for endpoint, requests in preprocessed_data.items():
    #     print(f"Endpoint: {endpoint}")
    #     for req in requests:
    #         print(f"  Method: {req['method']}")
    #         print(f"  Query Params: {req['query_params']}")
    #         print(f"  Headers: {req['headers']}")
    #         print(f"  Post Data: {req['post_data']}")
    #         print("-" * 40)

    # Save preprocessed data to a JSON file
    with open("preprocessed_requests.json", "w") as outfile:
        json.dump(preprocessed_data, outfile, indent=4)

    print(f"Preprocessed data saved to preprocessed_requests.json")
