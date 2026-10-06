import os
import json
import glob
import re

def build_aligned_dataset():
    print("Scanning data/adverse_media for matching articles...")
    pattern = os.path.join(os.path.dirname(__file__), "..", "data", "adverse_media", "**", "*.json")
    files = glob.glob(pattern, recursive=True)
    print(f"Total files available: {len(files)}")

    def get_links_for_keyword(kw, limit=15):
        matched = []
        seen = set()
        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    text = (data.get("text") or "") + " " + (data.get("title") or "")
                    if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                        thread = data.get("thread", {})
                        url = thread.get("url") or data.get("url")
                        title = thread.get("title") or data.get("title") or "Adverse Media Article"
                        site = thread.get("site") or "News Outlet"
                        if url and url.startswith("http") and url not in seen:
                            seen.add(url)
                            matched.append({
                                "url": url,
                                "title": title[:100],
                                "source_name": site
                            })
                            if len(matched) >= limit:
                                break
            except Exception:
                pass
        return matched

    # 1. Gautam Adani (Directly from dataset)
    adani_links = get_links_for_keyword("Adani", limit=18)
    # Ensure top Wikipedia anchor is present for high scraping success
    adani_links.insert(0, {
        "url": "https://en.wikipedia.org/wiki/Gautam_Adani",
        "title": "Gautam Adani - Wikipedia Compliance Record & Indictments",
        "source_name": "Wikipedia"
    })

    # 2. Sam Bankman-Fried (FTX / Crypto Fraud)
    sbf_links = [
        {"url": "https://en.wikipedia.org/wiki/Sam_Bankman-Fried", "title": "Sam Bankman-Fried Conviction & Sentencing", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Bankruptcy_of_FTX", "title": "Collapse and Bankruptcy of FTX Exchange", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Alameda_Research", "title": "Alameda Research Criminal Co-conspiracy", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Caroline_Ellison", "title": "Caroline Ellison Plea Agreement and Testimony", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Gary_Wang_(businessman)", "title": "Gary Wang FTX Fraud Testimony", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Nishad_Singh", "title": "Nishad Singh FTX Campaign Finance Findings", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Securities_fraud", "title": "Federal Securities Fraud Charges Overview", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Wire_fraud", "title": "Wire Fraud Statues and Case Precedents", "source_name": "Wikipedia"}
    ]

    # 3. Elon Musk (Directly from dataset)
    musk_links = get_links_for_keyword("Elon Musk", limit=15)
    musk_links.insert(0, {
        "url": "https://en.wikipedia.org/wiki/Elon_Musk",
        "title": "Elon Musk - Corporate Lawsuits & SEC Regulatory Scrutiny",
        "source_name": "Wikipedia"
    })

    # 4. Goldman Sachs (Directly from dataset)
    goldman_links = get_links_for_keyword("Goldman Sachs", limit=12)
    goldman_links.insert(0, {
        "url": "https://en.wikipedia.org/wiki/Goldman_Sachs",
        "title": "Goldman Sachs Legal Proceedings, 1MDB Settlement & Fines",
        "source_name": "Wikipedia"
    })

    # 5. False Positive Control (Intentional Noise to test false positive rejection)
    noise_links = [
        {"url": "https://en.wikipedia.org/wiki/Monetary_policy", "title": "Federal Reserve Monetary Policy Principles", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Inflation", "title": "Global Inflation Macroeconomic Report", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Interest_rate", "title": "Interest Rate Trends and Sovereign Debt", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/European_Central_Bank", "title": "European Central Bank Operating Framework", "source_name": "Wikipedia"},
        {"url": "https://en.wikipedia.org/wiki/Bank_of_Japan", "title": "Bank of Japan Yield Curve Control Overview", "source_name": "Wikipedia"}
    ]

    candidates = [
        {
            "candidate_id": "CAND-001-ADANI",
            "hit_id": "HIT-ADANI-2024",
            "entity_name": "Gautam Adani",
            "risk_category": "High Risk - US DOJ $265M Bribery Indictment & FCPA",
            "country": "India / United States",
            "description": "Billionaire industrialist indicted by US Federal Court in Brooklyn over alleged $265 million bribery scheme involving solar energy contracts.",
            "total_events": len(adani_links),
            "events": adani_links
        },
        {
            "candidate_id": "CAND-002-SBF",
            "hit_id": "HIT-FTX-CRIM",
            "entity_name": "Sam Bankman-Fried",
            "risk_category": "High Risk - Wire Fraud & Multibillion Embezzlement",
            "country": "Bahamas / United States",
            "description": "Founder of FTX crypto exchange convicted on 7 criminal fraud counts resulting in a 25-year federal prison sentence.",
            "total_events": len(sbf_links),
            "events": sbf_links
        },
        {
            "candidate_id": "CAND-003-MUSK",
            "hit_id": "HIT-MUSK-CORP",
            "entity_name": "Elon Musk",
            "risk_category": "Moderate Risk - SEC Inquiries & Board Governance",
            "country": "United States",
            "description": "Technology executive subject to regulatory reviews by the SEC, NLRB, and multiple corporate governance lawsuits.",
            "total_events": len(musk_links),
            "events": musk_links
        },
        {
            "candidate_id": "CAND-004-GOLDMAN",
            "hit_id": "HIT-GS-RISK",
            "entity_name": "Goldman Sachs",
            "risk_category": "Moderate Risk - Investment Write-down & Exposure",
            "country": "United States / Sweden",
            "description": "Global investment bank facing substantial multi-million dollar charges on European green battery manufacturer Northvolt write-downs.",
            "total_events": len(goldman_links),
            "events": goldman_links
        },
        {
            "candidate_id": "CAND-005-CONTROL-FP",
            "hit_id": "HIT-CONTROL-FALSE",
            "entity_name": "Viktor Petrov",
            "risk_category": "Verification Control - False Positive Rejection",
            "country": "Cyprus / Global",
            "description": "Control subject to verify that the LLM agent accurately identifies lack of adverse findings and does not hallucinate false positives.",
            "total_events": len(noise_links),
            "events": noise_links
        }
    ]

    # Save to src/data/candidate_hits.json
    backend_path = os.path.join(os.path.dirname(__file__), "..", "src", "data", "candidate_hits.json")
    with open(backend_path, "w", encoding="utf-8") as fp:
        json.dump(candidates, fp, indent=2)
    print(f"Updated {backend_path}")

    # Save to frontend/src/mockCandidates.ts
    frontend_ts_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "mockCandidates.ts")
    with open(frontend_ts_path, "w", encoding="utf-8") as fp:
        fp.write("import type { CandidateProfile } from './types';\n\n")
        fp.write("export const DEFAULT_CANDIDATES: CandidateProfile[] = ")
        json.dump(candidates, fp, indent=2)
        fp.write(";\n")
    print(f"Updated {frontend_ts_path}")

    print("\nCandidate directory successfully aligned with real adverse media articles!")
    for c in candidates:
        print(f"  [{c['candidate_id']}] {c['entity_name']} - {c['total_events']} events ({c['risk_category']})")

if __name__ == "__main__":
    build_aligned_dataset()

