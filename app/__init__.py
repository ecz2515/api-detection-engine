import json
import os

from flask import Flask, flash, render_template, request


def create_app():
    """Create and configure the Flask application.

    Returns:
        A configured Flask application instance
    """
    app = Flask(__name__)

    # Simple configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-for-testing")
    app.config["OUTPUT_DIR"] = os.environ.get("OUTPUT_DIR", "output")
    app.config["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
    app.config["OPENAI_MODEL"] = os.environ.get("OPENAI_MODEL", "gpt-4")

    # Route definitions
    @app.route("/", methods=["GET", "POST"])
    def index():
        """Main page route handler."""
        endpoints = None
        url_input = request.form.get("url", "")
        request_type = request.form.get("request_type", "GET")

        # Prepend 'http://' if the URL doesn't start with a protocol
        if url_input and not url_input.startswith(("http://", "https://")):
            url_input = "http://" + url_input

        if request.method == "POST":
            if not url_input:
                flash("Please provide a URL to analyze.")
                return render_template(
                    "index.html",
                    endpoints=endpoints,
                    url_input=url_input,
                    request_type=request_type,
                )

            try:
                # Import here to avoid circular imports
                from api_engine.pipeline import ApiDetectionPipeline

                # Create and run the API detection pipeline
                pipeline = ApiDetectionPipeline(
                    output_dir=app.config["OUTPUT_DIR"],
                    openai_api_key=app.config["OPENAI_API_KEY"],
                    openai_model=app.config["OPENAI_MODEL"],
                )

                success, output_file = pipeline.run(
                    url=url_input, request_type=request_type
                )

                if success and output_file:
                    # Load the output from necessary_headers.json
                    with open(output_file, "r") as f:
                        data = json.load(f)
                    endpoints = data.get("endpoints", [])
                else:
                    flash("Pipeline execution failed. Check logs for details.")

            except Exception as e:
                flash(f"An error occurred: {str(e)}")

        return render_template(
            "index.html",  # Fixed template name
            endpoints=endpoints,
            url_input=url_input,
            request_type=request_type,
        )

    return app
