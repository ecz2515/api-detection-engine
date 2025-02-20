from playwright.sync_api import sync_playwright

def capture_har(url, output_file="network_traffic.har"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(record_har_path=output_file)
        page = context.new_page()
        
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle")

        page.wait_for_timeout(5000)

        print(f"Saving HAR file to {output_file}...")
        context.close()
        browser.close()
        print("Done!")

capture_har("https://www.substack.com")
