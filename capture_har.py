from playwright.sync_api import sync_playwright

def capture_har(url, output_file="network_traffic.har"):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_har_path=output_file)
        page = context.new_page()
        
        print(f"Navigating to {url}...")
        page.goto(url)  
        page.wait_for_timeout(5000)  

        print(f"Saving HAR file to {output_file}...")
        context.close()
        browser.close()
        print("Done!")

import sys

if len(sys.argv) != 2:
    print("Usage: python capture_har.py <URL>")
    sys.exit(1)

url = sys.argv[1]
capture_har(url)
