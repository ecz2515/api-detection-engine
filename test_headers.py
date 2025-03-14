import json
import subprocess


def test_minimal_headers():
    with open("necessary_headers.json", "r") as f:
        header_data = json.load(f)

    print("Testing all endpoints...")
    failed_tests = []

    for entry in header_data["endpoints"]:
        base_url = entry["url"]
        method = entry["method"]

        try:
            result = subprocess.run(
                entry["curl_example"], shell=True, capture_output=True
            )

            if result.returncode == 0:
                print(f"✓ {method} {base_url} - Success")
            else:
                print(f"✗ {method} {base_url} - Failed")
                try:
                    error = result.stderr.decode("utf-8")
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
