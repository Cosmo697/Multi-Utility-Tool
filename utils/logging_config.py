# utils/logging_config.py

import logging
import os

def setup_logging():
    """
    Set up logging configuration to log messages to both a file and the console.
    """
    try:
        # Create logs directory if it does not exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            print("Created logs directory.")

        # Setup logging configuration
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler("logs/app.log"),
                logging.StreamHandler()
            ]
        )

        # Log initial information
        logger = logging.getLogger(__name__)
        logger.info("Logging setup complete.")
    except Exception as e:
        print(f"Error setting up logging: {e}")
        raise

# If this module is run directly, set up logging
if __name__ == "__main__":
    setup_logging()
