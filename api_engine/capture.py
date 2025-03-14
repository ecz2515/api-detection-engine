import json

from playwright.sync_api import sync_playwright

from utils.logger import get_logger

logger = get_logger(__name__)


class HarCapture:
    """Captures network traffic in HAR format using Playwright."""

    def __init__(self, timeout=5000):
        """Initialize the HAR capture with configurable timeout.

        Args:
            timeout: Time to wait after page load in milliseconds
        """
        self.timeout = timeout

    def capture(self, url, output_file=None):
        """Capture HAR data from the given URL.

        Args:
            url: The URL to navigate to
            output_file: Optional path to save the HAR file

        Returns:
            tuple: (success, har_data_dict)
        """
        try:
            # Add protocol if missing
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url

            logger.info(f"Capturing HAR data for {url}")
            temp_har_path = "temp_capture.har"

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(record_har_path=temp_har_path)
                page = context.new_page()

                logger.info(f"Navigating to {url}...")
                page.goto(url)
                page.wait_for_timeout(self.timeout)

                logger.info("Closing browser and collecting HAR data...")
                context.close()
                browser.close()

                # Load the HAR data from the temporary file
                with open(temp_har_path, "r") as f:
                    har_data = json.load(f)

                # Optionally save to the specified output file
                if output_file:
                    with open(output_file, "w") as f:
                        json.dump(har_data, f)
                    logger.info(f"HAR file saved to {output_file}")

                logger.info("HAR capture completed successfully")

            return True, har_data

        except Exception as e:
            logger.error(f"Failed to capture HAR: {str(e)}")
            return False, None
