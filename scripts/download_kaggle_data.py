import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# The Kaggle API requires KAGGLE_USERNAME and KAGGLE_KEY
# If the user provided KAGGLE_API_TOKEN, map it over.
if 'KAGGLE_KEY' not in os.environ and 'KAGGLE_API_TOKEN' in os.environ:
    os.environ['KAGGLE_KEY'] = os.environ['KAGGLE_API_TOKEN']

# Import kaggle AFTER environment variables are set so it authenticates properly
import kaggle

def download_adverse_media():
    dataset_name = "gevaran/adverse-media-news-dataset-repository"
    download_path = "data/adverse_media"
    
    os.makedirs(download_path, exist_ok=True)
    
    print(f"Authenticating with Kaggle as {os.environ.get('KAGGLE_USERNAME')}...")
    kaggle.api.authenticate()
    
    print(f"Downloading Kaggle dataset: {dataset_name}...")
    kaggle.api.dataset_download_files(dataset_name, path=download_path, unzip=True)
    
    print(f"Dataset downloaded and unzipped successfully to {download_path}!")
    
    # List the downloaded files
    files = os.listdir(download_path)
    print(f"Files available: {files}")

if __name__ == "__main__":
    download_adverse_media()
