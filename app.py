import json
import subprocess

from flask import Flask, flash, render_template, request

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Needed for flash messages


@app.route("/", methods=["GET", "POST"])
def index():
    endpoints = None
    url_input = request.form.get("url", "")
    request_type = request.form.get("request_type", "")

    # Prepend 'http://' if the URL doesn't start with 'http://' or 'https://'
    if url_input and not url_input.startswith(("http://", "https://")):
        url_input = "http://" + url_input

    if request.method == "POST":
        if not url_input or not request_type:
            flash("Please provide both a URL and a request type.")
            return render_template(
                "index.html",
                endpoints=endpoints,
                url_input=url_input,
                request_type=request_type,
            )

        try:
            # Run build.sh with the provided URL and request type
            subprocess.run(["./build.sh", url_input, request_type], check=True)
            # Load the output from necessary_headers.json
            with open("necessary_headers.json", "r") as f:
                data = json.load(f)
            endpoints = data.get("endpoints", [])
        except subprocess.CalledProcessError as e:
            flash(f"Build failed: {str(e)}")
        except Exception as e:
            flash(f"An error occurred: {str(e)}")

    return render_template(
        "index.html",
        endpoints=endpoints,
        url_input=url_input,
        request_type=request_type,
    )


if __name__ == "__main__":
    app.run(debug=True)
