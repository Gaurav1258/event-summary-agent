import os
import sys
from dotenv import load_dotenv

# Ensure Python can find our 'src' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.gcs_client import GCSDataClient

def test_gcs_fetch():
    load_dotenv()
    
    project_id = os.environ.get("GCP_PROJECT_ID")
    # Replace with your actual bucket name if different
    bucket_name = "mlops2215-adverse-media"
    
    if not project_id:
        print("Please ensure GCP_PROJECT_ID is set in your .env file.")
        return

    print(f"Connecting to GCP Project: {project_id}")
    print(f"Target Bucket: {bucket_name}")
    
    client = GCSDataClient(project_id=project_id, bucket_name=bucket_name)
    
    # We will look inside the Datasets folder we uploaded
    print("\nFetching up to 5 URLs from the bucket...")
    
    # You might need to adjust the prefix if your folder structure differs slightly in GCS
    links = client.extract_urls_from_directory(prefix="Datasets/", max_files=5)
    
    print(f"\nExtracted {len(links)} links successfully!")
    for link in links:
        print(f"- {link.url} (Source: {link.source_name})")

if __name__ == "__main__":
    test_gcs_fetch()
