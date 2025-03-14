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

    def capture(self, url, output_file="network_traffic.har"):
        """Capture HAR data from the given URL.

        Args:
            url: The URL to navigate to
            output_file: Path to save the HAR file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add protocol if missing
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url

            logger.info(f"Capturing HAR data for {url}")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(record_har_path=output_file)
                page = context.new_page()

                logger.info(f"Navigating to {url}...")
                page.goto(url)
                page.wait_for_timeout(self.timeout)

                logger.info(f"Saving HAR file to {output_file}...")
                context.close()
                browser.close()
                logger.info("HAR capture completed successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to capture HAR: {str(e)}")
            return False
