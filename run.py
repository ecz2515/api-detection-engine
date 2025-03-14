import argparse

from dotenv import load_dotenv

from app import create_app

# Load environment variables
load_dotenv()

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API Detection Engine")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to run the server on",
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port to run the server on"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Override debug setting if specified
    if args.debug:
        app.debug = True

    app.run(host=args.host, port=args.port)
