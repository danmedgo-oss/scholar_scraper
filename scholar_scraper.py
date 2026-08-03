import os
import json
import re
import pandas as pd
from serpapi import GoogleSearch


SHEET_URL = "https://docs.google.com/spreadsheets/d/12YLMeZbR_CEzCbmnLE7V0FuxffjhL2IUlteBCAXMEEM/export?format=csv"
OUTPUT_FILE = "scholar_data.json"

def get_scholar_ids_from_sheet(sheet_url):
    author_ids = []
    try:
        df = pd.read_csv(sheet_url)
        for col in df.columns:
            for val in df[col].dropna():
                match = re.search(r"user=([a-zA-Z0-9_-]+)", str(val))
                if match:
                    author_id = match.group(1)
                    if author_id not in author_ids:
                        author_ids.append(author_id)
    except Exception as e:
        print(f"Error reading google sheet: {e}")
    return author_ids

def fetch_author_rag_data(author_id):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("Error: SERPAPI_KEY not found")
        return None

    print(f"Fetching data for Scholar ID: {author_id}")
    params = {
        "engine": "google_scholar_author",
        "author_id": author_id,
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
    except Exception as e:
        print(f"Error connecting to serpapi: {e}")
        return None

    if "author" not in results:
        return None

    author_info = results.get("author", {})
    articles = results.get("articles", [])

    cites = 0
    h_idx = 0
    for row in results.get("cited_by", {}).get("table", []):
        if "citations" in row:
            cites = row.get("citations", {}).get("all", 0)
        elif "h_index" in row:
            h_idx = row.get("h_index", {}).get("all", 0)

    metadata = {
        "id": author_id,
        "nm": author_info.get("name", ""),
        "aff": author_info.get("affiliations", ""),
        "int": [i.get("title", "") for i in author_info.get("interests", [])],
        "cite": cites,
        "h": h_idx
    }
    metadata = {k: v for k, v in metadata.items() if v}

    pubs = []
    for article in articles:
        pub = {
            "t": article.get("title", ""),
            "y": article.get("year", ""),
            "c": article.get("cited_by", {}).get("value", 0),
            "u": article.get("link", "")
        }
        pub = {k: v for k, v in pub.items() if v}
        pubs.append(pub)

    return {"m": metadata, "p": pubs}

def main():
    author_ids = get_scholar_ids_from_sheet(SHEET_URL)
    print(f"Found author IDs from sheet: {author_ids}")

    all_authors_data = []
    for uid in author_ids:
        data = fetch_author_rag_data(uid)
        if data:
            all_authors_data.append(data)
            print(f"Successfully fetched {uid}")
        else:
            print(f"Skipped ID: {uid}")

    if all_authors_data:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_authors_data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"Saved minified data to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
