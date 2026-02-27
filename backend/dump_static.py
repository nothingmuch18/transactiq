import os
import requests
import json

BASE_URL = "http://localhost:8000/api"
OUT_DIR = "../frontend/public/data"

os.makedirs(OUT_DIR, exist_ok=True)

endpoints = [
    ("/overview", "overview.json"),
    ("/insights", "insights.json"),
    ("/risk", "risk.json"),
    ("/quality", "quality.json"),
    ("/schema", "schema.json"),
    ("/preview?limit=50", "preview.json"),
]

for url, filename in endpoints:
    print(f"Fetching {url}...")
    try:
        res = requests.get(f"{BASE_URL}{url}")
        res.raise_for_status()
        with open(os.path.join(OUT_DIR, filename), "w") as f:
            json.dump(res.json(), f)
        print(f"Saved {filename}")
    except Exception as e:
        print(f"Failed {url}: {e}")

# POST endpoints (Anomalies)
print("Fetching /anomalies...")
res = requests.post(f"{BASE_URL}/anomalies", json={})
with open(os.path.join(OUT_DIR, "anomalies.json"), "w") as f:
    json.dump(res.json(), f)

print("Done generating static data!")
