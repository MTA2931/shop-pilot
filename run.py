"""ShopPilot application entry point.

Run with:  python run.py
or:        flask --app app run
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file if present (never committed to version control)
load_dotenv()

from app import create_app

config_name = os.environ.get("FLASK_CONFIG", "default")
app = create_app(config_name)

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host=host, port=port, debug=debug)
