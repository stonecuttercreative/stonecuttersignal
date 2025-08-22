# BEGIN stonecutter extension: logging configuration
import logging

# Configure logger for the stonecutter package
logger = logging.getLogger("stonecutter")
logger.setLevel(logging.INFO)

# Only add handler if it doesn't already exist
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Prevent duplicate logs
logger.propagate = False
# END stonecutter extension