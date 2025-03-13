# API Detection Engine

A powerful tool for analyzing and detecting valuable API endpoints from web traffic, with automatic header optimization and documentation generation.

## Features

- 🔍 **HAR Traffic Analysis**: Captures and analyzes HTTP Archive (HAR) files to identify API endpoints
- 🤖 **AI-Powered Analysis**: Uses GPT-4 to identify valuable endpoints and assess their usefulness
- 🔑 **Header Optimization**: Automatically determines minimal required headers for successful API requests
- 📝 **Documentation Generation**: Creates comprehensive documentation for discovered endpoints
- 🌐 **Web Interface**: User-friendly web interface for running the analysis pipeline
- 🔄 **Pipeline Automation**: Single command to run the entire analysis process

## Prerequisites

- Python 3.x
- Node.js (for web dependencies)
- OpenAI API key (for endpoint analysis)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/api-detection-engine.git
cd api-detection-engine
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
npm install
```

4. Create a `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Web Interface

1. Start the Flask application:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:5000`
3. Enter a URL and select the request type (GET, POST, PUT, DELETE)
4. Click "Run Pipeline" to start the analysis

### Command Line

Run the complete analysis pipeline using the build script:
```bash
./build.sh <URL> <REQUEST_TYPE>
```

Example:
```bash
./build.sh https://example.com GET
```

## Pipeline Steps

1. **HAR Capture** (`capture_har.py`): Captures network traffic in HAR format
2. **Request Filtering** (`har_filter_requests.py`): Filters and preprocesses HAR logs
3. **LLM Analysis** (`llm_process.py`): Analyzes endpoints using GPT-4 to identify valuable data
4. **Request Matching** (`match_har_requests.py`): Matches processed requests with valuable endpoints
5. **Header Optimization** (`find_necessary_headers.py`): Determines minimal required headers

## Output Files

- `network_traffic.har`: Raw captured network traffic
- `filtered_requests.json`: Preprocessed and filtered requests
- `analyzed_endpoints.json`: AI analysis results of endpoint value
- `matched_requests.json`: Matched valuable requests
- `necessary_headers.json`: Optimized headers for each endpoint

## Web Interface

The web interface provides:
- URL and request type input
- Pipeline execution controls
- Results display with:
  - Endpoint URLs
  - Usefulness scores
  - Required headers
  - Example cURL commands
  - Parameter documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4 API
- Playwright for browser automation
- Flask for web interface
