#!/usr/bin/env python3
"""
Flask web application runner for Engineering Design Criteria Extractor.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from a .env file if present (helps packaged apps)
try:
    from dotenv import load_dotenv
    # Load .env from current working directory or alongside the executable
    load_dotenv()
except Exception:
    # dotenv is optional at runtime; ignore if unavailable
    pass

from src.webapp.app import create_app

if __name__ == "__main__":
    app = create_app()
    
    # Get configuration from environment
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    print(f"🚀 Starting Engineering Design Criteria Extractor Web App")
    print(f"📍 Server: http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📁 Output folder: {app.config['OUTPUT_FOLDER']}")
    print("=" * 60)
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1) 