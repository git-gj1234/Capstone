import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

# Check for required environment variables
required_env_vars = ['GEMINI_API_KEY']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

if missing_vars:
    logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logging.error("Please set these variables before running the application")
    print("\n" + "*" * 80)
    print("ENVIRONMENT VARIABLE ERROR:")
    print(f"The following required environment variables are missing: {', '.join(missing_vars)}")
    print("\nTo fix this issue:")
    print("1. Make sure to set GEMINI_API_KEY in your environment")
    print("   - On Windows: set GEMINI_API_KEY=your_api_key")
    print("   - On macOS/Linux: export GEMINI_API_KEY=your_api_key")
    print("2. Or add these lines at the top of this script for testing (not for production):")
    print('   import os')
    print('   os.environ["GEMINI_API_KEY"] = "your_api_key_here"')
    print("*" * 80 + "\n")
    
    # Continue execution but with warnings
    logging.warning("Application will start but functionality may be limited")

# Import the Flask app
from app import app

if __name__ == "__main__":
    logging.info("Starting Flask application on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
