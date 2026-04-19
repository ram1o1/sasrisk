import os

# Get the absolute path of the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define data directories
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

# Ensure directories exist when config is loaded
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)