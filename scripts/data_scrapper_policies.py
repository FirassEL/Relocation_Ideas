import os
import json
import requests

STATE_FILE = "state.json"  # track last page
JSON_FILE = "data/state_department_documents.json" # the output file
AGENCY_SLUG = "state-department" # agency filter for Federal Register 
DOCUMENT_TYPES = ["RULE", "PRORULE"] # document types to fetch
PER_PAGE = 20 # number of documents per page (may be less if not enough results)
KEYWORDS = [ # keywords to filter documents
    "Hong Kong", # example using a nation as a key word 
    "non-immigrant", # example using a visa type as a key words
    "Visa",
    "F-1",
    "J-1",
    "B-1/B-2",
    "H-1B",
    "E-2 Visa",
]

# -------------------
# State helpers
# -------------------
def get_last_page(): # retrieve last processed page from state file
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("last_page", 0)
    return 0

def save_last_page(page): # save last processed page to state file
    with open(STATE_FILE, "w") as f:
        json.dump({"last_page": page}, f)

# -------------------
# Pipeline steps
# -------------------
def extract_page(page): # extract documents from a specific page
    resp = requests.get(
        "https://www.federalregister.gov/api/v1/documents.json",
        params={
            "conditions[agencies][]": AGENCY_SLUG,
            "conditions[type][]": DOCUMENT_TYPES,
            "per_page": PER_PAGE,
            "order": "newest",
            "page": page,
        },
    )
    resp.raise_for_status()
    return resp.json().get("results", [])

def transform_docs(docs, seen_ids): # transform and filter documents based on keywords
    processed = []
    for d in docs:
        doc_id = d.get("document_number")
        if doc_id in seen_ids:
            continue

        # Fetch full JSON
        detail = requests.get(f"https://www.federalregister.gov/api/v1/documents/{doc_id}.json").json()
        raw_text_url = detail.get("raw_text_url", "")
        full_text = ""
        supplementary_info = ""

        if raw_text_url:
            try:
                r = requests.get(raw_text_url, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
                full_text = r.text
                si_index = full_text.upper().find("SUPPLEMENTARY INFORMATION:")
                if si_index != -1:
                    supplementary_info = full_text[si_index + len("SUPPLEMENTARY INFORMATION:"):].strip()
            except:
                pass

        combined_text = " ".join([
            detail.get("title", ""),
            detail.get("abstract") or "",
            detail.get("excerpts") or "",
            supplementary_info,
            full_text
        ]).lower()

        matched_keywords = [kw for kw in KEYWORDS if kw.lower() in combined_text]
        if matched_keywords: # only keep documents that match keywords
            processed.append({ # structure the processed document
                "document_number": detail.get("document_number"), # unique ID
                "title": detail.get("title"), # document title
                "abstract": detail.get("abstract"), # document abstract
                "id": detail.get("id"), # internal ID
                "publication_date": detail.get("publication_date"), # publication date
                "dates": detail.get("dates"), # relevant dates, may contain date of effect
                "raw_text_url": raw_text_url, # URL to fetch full text
                "html_url": detail.get("html_url"), # URL to HTML version
                "matched_keywords": matched_keywords, # keywords that matched
                "supplementary_information": supplementary_info, # extracted supplementary info section
                "action": detail.get("action"), # action taken by the document
                "type": detail.get("type"), # document type
            })
            seen_ids.add(doc_id) # mark this ID as seen, to avoid duplicates in this run
    return processed

def load_docs(processed): # load processed documents into JSON file
    if os.path.exists(JSON_FILE): 
        with open(JSON_FILE, "r") as f:
            all_data = json.load(f)
    else:
        all_data = []

    all_data.extend(processed)
    with open(JSON_FILE, "w") as f:
        json.dump(all_data, f, indent=2)
    return len(processed)

# -------------------
# Run pipeline
# -------------------
def run_pipeline():
    last_page = get_last_page()
    next_page = last_page + 1

    docs = extract_page(next_page)
    if not docs:
        print("⚠ No new documents found.")
        return

    seen_ids = {doc["document_number"] for doc in json.load(open(JSON_FILE, "r"))} if os.path.exists(JSON_FILE) else set()
    processed = transform_docs(docs, seen_ids)
    count = load_docs(processed)

    save_last_page(next_page)
    print(f"✅ Loaded {count} documents from page {next_page}")

if __name__ == "__main__":
    run_pipeline()
