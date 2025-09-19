import requests
import json
import os

# -------------------
# Config
# -------------------
JSON_FILE = "data/school_data.json"
BASE_URL = "https://data.sfgov.org/resource/tpp3-epx2.json"
PER_PAGE = 5000  # max limit per request


# -------------------
# Extract
# -------------------
def extract_schooldata(offset=0):
    resp = requests.get(
        BASE_URL,
        params={
            "$limit": PER_PAGE,
            "$offset": offset
        },
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp.raise_for_status()
    return resp.json()


# -------------------
# Load to JSON
# -------------------
def load_docs(data):
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            all_data = json.load(f)
    else:
        all_data = []

    all_data.extend(data)

    with open(JSON_FILE, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"✅ Saved {len(data)} new records, total {len(all_data)}")


# -------------------
# Runner
# -------------------
if __name__ == "__main__":
    offset = 0
    while True:
        print(f"Fetching records starting at offset {offset}...")
        data = extract_schooldata(offset=offset)
        if not data:
            print("No more data found. Done.")
            break

        load_docs(data)
        offset += PER_PAGE
