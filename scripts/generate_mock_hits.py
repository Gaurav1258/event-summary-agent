import pandas as pd
from datasets import load_dataset
import json
import os
import random

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

def generate_mock_data():
    print("Downloading OpenSanctions dataset for candidate entities...")
    try:
        # Load the open sanctions dataset
        dataset = load_dataset("sanctions-er-anon/opensanctions_pairs", split="train")
        df = dataset.to_pandas()
        
        print(f"Dataset loaded. Columns available: {df.columns.tolist()}")
        
        # Take a small sample of 5 rows to create our mock screening hits
        sample = df.head(5)
        
        mock_hits = []
        
        for idx, row in sample.iterrows():
            # The exact schema depends on the dataset, we'll extract generic properties
            # and simulate the "100 events per candidate" problem!
            num_links = random.randint(20, 100)
            
            # Generating dummy event URLs to simulate adverse media/list links
            events = [
                f"https://news.example.com/article/{random.randint(10000, 99999)}/investigation" 
                for _ in range(num_links)
            ]
            
            # Constructing a simulated API request payload
            mock_hit = {
                "candidate_id": f"CAND-{1000 + idx}",
                # Just grabbing the first column's value as a placeholder name/ID for now
                "entity_context": str(row.iloc[0]), 
                "hit_id": f"HIT-{random.randint(100000, 999999)}",
                "total_events": num_links,
                "event_links": events
            }
            mock_hits.append(mock_hit)
            
        with open("data/mock_hits.json", "w") as f:
            json.dump(mock_hits, f, indent=4)
            
        print(f"Successfully generated {len(mock_hits)} mock hits in data/mock_hits.json")
        print("This file simulates the exact payload our agent will receive from the screening engine.")
        
    except Exception as e:
        print(f"Error fetching dataset: {e}")
        print("Note: If the dataset is gated, make sure you accept the conditions on HuggingFace and use your HF_TOKEN.")

if __name__ == "__main__":
    generate_mock_data()

