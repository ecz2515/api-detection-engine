import json

from flask import Blueprint, current_app, flash, render_template, request

from api_engine.pipeline import ApiDetectionPipeline

# Blueprint for the main routes
main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
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
            # Create and run the API detection pipeline
            pipeline = ApiDetectionPipeline(
                output_dir=current_app.config["OUTPUT_DIR"],
                openai_api_key=current_app.config["OPENAI_API_KEY"],
                openai_model=current_app.config["OPENAI_MODEL"],
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
        "index.html",
        endpoints=endpoints,
        url_input=url_input,
        request_type=request_type,
    )
