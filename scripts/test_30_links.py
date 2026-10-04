import json
import time
import httpx
import os

CLOUD_RUN_URL = "https://event-summary-agent-vu53wmoyqa-uc.a.run.app/api/v1/summarize"
PAYLOAD_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sample_30_links.json")

def run_30_link_test():
    print("=" * 60)
    print("🚀 TESTING 30-LINK MAP-REDUCE ON LIVE CLOUD RUN AGENT")
    print(f"Target: {CLOUD_RUN_URL}")
    print("=" * 60)

    with open(PAYLOAD_FILE, "r") as f:
        payload = json.load(f)

    total_links = len(payload["events"])
    print(f"\nCandidate: {payload['entity_name']} (ID: {payload['candidate_id']})")
    print(f"Total Event Links to Process: {total_links}")
    print("Sending request to Cloud Run (Scraping + Gemini Map-Reduce)...\n")

    start_time = time.time()
    
    # 30 links involves concurrent web scraping + 30 Map calls + 1 Reduce call
    # Timeout set to 300s to accommodate full processing
    with httpx.Client(timeout=300.0) as client:
        response = client.post(CLOUD_RUN_URL, json=payload)

    elapsed = time.time() - start_time

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS in {elapsed:.2f} seconds!\n")
        print("--- Scraping Statistics ---")
        print(f"Total Links:       {data['stats']['total_links']}")
        print(f"Successful Scrapes: {data['stats']['successful_scrapes']}")
        print(f"Failed Scrapes:     {data['stats']['failed_scrapes']}")
        print("\n" + "=" * 60)
        print("📄 FINAL INVESTIGATOR SUMMARY REPORT")
        print("=" * 60 + "\n")
        print(data["summary_report"])
        print("\n" + "=" * 60)
    else:
        print(f"❌ FAILED with status code {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    run_30_link_test()
