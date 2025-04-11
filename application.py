import os

from dotenv import load_dotenv

from app import create_app

# Load environment variables
load_dotenv()

# Create the Flask application
application = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    application.run(host=host, port=port, debug=debug)
