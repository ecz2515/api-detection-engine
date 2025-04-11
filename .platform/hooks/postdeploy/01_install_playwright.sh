#!/bin/bash
# Script to install Playwright browsers

echo "Running postdeploy script to install Playwright browsers..."

# Navigate to the application directory where requirements.txt was installed
# Note: The exact path might vary slightly based on the platform version,
# /var/app/current is common for Amazon Linux 2 platforms.
APP_DIR="/var/app/current"

if [ -d "$APP_DIR" ]; then
  cd "$APP_DIR"

  echo "Current directory: $(pwd)"
  echo "Attempting to install Playwright Chromium browser..."

  # It's crucial to run this with the correct Python environment
  # Option 1: If 'python' or 'python3' in PATH points to the virtual env (common in newer EB platforms)
  # playwright install chromium --with-deps

  # Option 2: Explicitly use the Python from the virtual environment EB creates
  # Usually located at /var/app/venv/staging-LQMOB6/bin/python (path might vary)
  # Find the python executable in the virtual environment
  PYTHON_EXEC=$(find /var/app/venv/ -type f -name python | head -n 1)

  if [ -z "$PYTHON_EXEC" ]; then
     echo "Could not find Python executable in /var/app/venv/. Trying default python3."
     PYTHON_EXEC=python3 # Fallback
  fi

  echo "Using Python executable: $PYTHON_EXEC"

  # Run playwright install using the specific python environment
  # Adding --with-deps attempts to install needed system libraries (requires sudo, often fails here)
  # It's better to install deps via .ebextensions if needed (see Step 4 alternative)
  $PYTHON_EXEC -m playwright install chromium

  # Check exit code
  if [ $? -eq 0 ]; then
    echo "Playwright Chromium installation successful."
  else
    echo "Playwright Chromium installation failed. Check logs." >&2
    # Optionally, fail the deployment by exiting with non-zero status
    # exit 1
  fi

else
  echo "Application directory $APP_DIR not found." >&2
  # exit 1 # Optionally fail deployment
fi

echo "Finished postdeploy script."