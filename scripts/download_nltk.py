import nltk
import os

# The directory where the data will be stored, same as the ENV in Dockerfile
DOWNLOAD_DIR = os.getenv("NLTK_DATA", "/app/nltk_data")

# Create the directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Download the required packages to the specified directory
nltk.download("averaged_perceptron_tagger", download_dir=DOWNLOAD_DIR)
nltk.download("punkt", download_dir=DOWNLOAD_DIR)

print(f"NLTK packages downloaded successfully to {DOWNLOAD_DIR}")
