import json
import logging
from typing import List
from google.cloud import storage

from .schema import EventLink

logger = logging.getLogger(__name__)

class GCSDataClient:
    """
    Client to interact with Google Cloud Storage. 
    Used to fetch screening events (Kaggle mock data) directly from the cloud bucket.
    """
    def __init__(self, project_id: str, bucket_name: str):
        self.project_id = project_id
        self.bucket_name = bucket_name
        # The storage client will automatically use the Application Default Credentials 
        # we set up earlier via `gcloud auth application-default login`
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)

    def extract_urls_from_directory(self, prefix: str = "", max_files: int = 100) -> List[EventLink]:
        """
        Scans the GCS bucket for JSON files, downloads them into memory, 
        and extracts ONLY the URLs (ignoring the pre-scraped text).
        """
        logger.info(f"Scanning gs://{self.bucket_name}/{prefix} for up to {max_files} articles...")
        
        blobs = self.bucket.list_blobs(prefix=prefix)
        event_links = []
        count = 0
        
        for blob in blobs:
            if count >= max_files:
                break
                
            if blob.name.endswith(".json"):
                try:
                    # Download the JSON content into memory
                    content = blob.download_as_text()
                    data = json.loads(content)
                    
                    # Extract the URL as requested, strictly ignoring the "text" field
                    if "url" in data:
                        event_links.append(
                            EventLink(
                                url=data["url"], 
                                source_name=f"gs://{self.bucket_name}/{blob.name}"
                            )
                        )
                        count += 1
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON in blob: {blob.name}")
                except Exception as e:
                    logger.error(f"Unexpected error reading {blob.name}: {e}")
                    
        logger.info(f"Successfully extracted {len(event_links)} URLs from GCS.")
        return event_links
