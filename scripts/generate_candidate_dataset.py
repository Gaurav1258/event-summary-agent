import os
import json
import glob
import random

def generate_candidate_hits():
    print("Scanning data/adverse_media for articles...")
    
    pattern = os.path.join(os.path.dirname(__file__), "..", "data", "adverse_media", "**", "*.json")
    files = glob.glob(pattern, recursive=True)
    
    print(f"Found {len(files)} total article files.")
    
    extracted_articles = []
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Check for thread.url or url
                thread = data.get("thread", {})
                url = thread.get("url") or data.get("url")
                title = thread.get("title") or data.get("title") or "Adverse Media Event"
                site = thread.get("site") or "News Source"
                
                if url and url.startswith("http"):
                    extracted_articles.append({
                        "url": url,
                        "title": title[:100],
                        "source_name": site
                    })
        except Exception:
            continue
            
    print(f"Successfully extracted {len(extracted_articles)} valid URLs with metadata.")
    
    if not extracted_articles:
        print("No articles found in data/adverse_media. Generating synthetic fallback.")
        return

    # Shuffle for realistic distribution
    random.seed(42)
    random.shuffle(extracted_articles)

    # Define 5 realistic candidate screening profiles
    candidate_profiles = [
        {
            "candidate_id": "CAND-001-SANCTION",
            "hit_id": "HIT-90141",
            "entity_name": "Viktor Petrov",
            "risk_category": "High Risk - International Sanctions & Money Laundering",
            "country": "Cyprus / Russia",
            "link_count": 25,
            "description": "Politically exposed person flagged in multiple offshore financial shell investigations."
        },
        {
            "candidate_id": "CAND-002-FRAUD",
            "hit_id": "HIT-88234",
            "entity_name": "Elizabeth Holmes",
            "risk_category": "High Risk - Securities & Wire Fraud",
            "country": "United States",
            "link_count": 18,
            "description": "Former healthcare tech executive convicted of investor fraud and false claims."
        },
        {
            "candidate_id": "CAND-003-CORP-BRIBERY",
            "hit_id": "HIT-74190",
            "entity_name": "Odebrecht Global Holding",
            "risk_category": "Moderate Risk - Foreign Corrupt Practices Act (FCPA)",
            "country": "Brazil",
            "link_count": 12,
            "description": "Conglomerate involved in historical cross-border bribery scandals with active monitorship."
        },
        {
            "candidate_id": "CAND-004-FALSE-POSITIVE",
            "hit_id": "HIT-33219",
            "entity_name": "Michael Chang",
            "risk_category": "Low Risk - Probable False Positive",
            "country": "Hong Kong / Canada",
            "link_count": 15,
            "description": "Common name collision against adverse news on unrelated financial fraud cases."
        },
        {
            "candidate_id": "CAND-005-STRESS-TEST",
            "hit_id": "HIT-99999",
            "entity_name": "Sam Bankman-Fried",
            "risk_category": "Stress Test - High Volume 50 Events",
            "country": "Bahamas / United States",
            "link_count": 50,
            "description": "High-volume screening hit designed to test parallel scraping and Map-Reduce synthesis."
        }
    ]

    candidate_hits = []
    idx = 0
    for profile in candidate_profiles:
        count = profile["link_count"]
        links = extracted_articles[idx:idx + count]
        idx += count
        
        candidate_hits.append({
            "candidate_id": profile["candidate_id"],
            "hit_id": profile["hit_id"],
            "entity_name": profile["entity_name"],
            "risk_category": profile["risk_category"],
            "country": profile["country"],
            "description": profile["description"],
            "total_events": len(links),
            "events": links
        })

    # Save to data/candidate_hits.json
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "candidate_hits.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(candidate_hits, f, indent=2)
        
    print(f"\nGenerated {len(candidate_hits)} candidates in {out_path}!")
    for c in candidate_hits:
        print(f"  - [{c['candidate_id']}] {c['entity_name']} ({c['total_events']} adverse media links)")

if __name__ == "__main__":
    generate_candidate_hits()
