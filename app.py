```python
# app.py
import os
import logging
from urllib.parse import urlparse

import requests
from flask import Flask, request, jsonify, abort
from flask.logging import default_handler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
HOST = os.getenv("FLASK_HOST", "0.0.0.0")
PORT = int(os.getenv("FLASK_PORT", 5000))
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 10))

# Initialize Flask app
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

# Setup logging
logger = logging.getLogger("bypass_api")
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
default_handler.setFormatter(formatter)
logger.addHandler(default_handler)


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


@app.errorhandler(400)
def handle_400(error):
    logger.warning(f"Bad request: {error}")
    return jsonify({"success": False, "error": "Bad Request", "message": str(error)}), 400


@app.errorhandler(404)
def handle_404(error):
    logger.warning(f"Not found: {error}")
    return jsonify({"success": False, "error": "Not Found", "message": str(error)}), 404


@app.errorhandler(500)
def handle_500(error):
    logger.exception("Internal server error")
    return jsonify({"success": False, "error": "Internal Server Error", "message": "An unexpected error occurred"}), 500


@app.route("/bypass", methods=["GET"])
def bypass():
    """
    Bypass a link by following redirects and returning the final destination URL.
    Query Parameters:
        url (str): The URL to bypass.
    """
    try:
        raw_url = request.args.get("url", "").strip()
        if not raw_url:
            abort(400, description="Missing 'url' query parameter")

        if not is_valid_url(raw_url):
            abort(400, description="Invalid URL format")

        logger.info(f"Bypassing URL: {raw_url}")

        # Perform a HEAD request first to avoid downloading large bodies
        try:
            resp = requests.head(raw_url, allow_redirects=True, timeout=TIMEOUT)
            final_url = resp.url
        except requests.RequestException:
            # Fallback to GET if HEAD fails (some servers reject HEAD)
            resp = requests.get(raw_url, allow_redirects=True, timeout=TIMEOUT, stream=True)
            final_url = resp.url

        logger.debug(f"Final URL after redirects: {final_url}")

        return jsonify(
            {
                "success": True,
                "original_url": raw_url,
                "bypassed_url": final_url,
            }
        ), 200

    except Exception as e:
        logger.exception("Error while processing bypass request")
        abort(500, description=str(e))


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
```

```bash
# requirements.txt
Flask==3.0.3
requests==2.32.3
python-dotenv==1.0.1
```

```bash
# .env (example)
FLASK_DEBUG=true
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
REQUEST_TIMEOUT=10
```

**Run**

```bash
pip install -r requirements.txt
python app.py
```

**Usage**

```bash
curl "http://localhost:5000/bypass?url=https://short.url/example"
```

Returns JSON with the final bypassed URL.