import os
import json
import re
import pandas as pd
from serpapi import GoogleSearch

SHEET_URL = "https://docs.google.com/spreadsheets/d/12YLMeZbR_CEzCbmnLE7V0FuxffjhL2IUlteBCAXMEEM/export?format=csv"
OUTPUT_FILE = "scholar_data.json"


def get_authors_from_sheet(sheet_url):
    authors_info = []
    try:
        df = pd.read_csv(sheet_url)
        for _, row in df.iterrows():
            link = ""
            for col in df.columns:
                val = str(row[col])
                if "scholar.google.com" in val:
                    link = val
                    break
            
            if link:
                match = re.search(r"user=([a-zA-Z0-9_-]+)", link)
                if match:
                    author_id = match.group(1)
                    thai_name = str(row.get("ชื่อ", "")) if pd.notna(row.get("ชื่อ", "")) else ""
                    eng_name = str(row.get("Name", "")) if pd.notna(row.get("Name", "")) else ""
                    
                    authors_info.append({
                        "id": author_id,
                        "thai_name": thai_name.strip(),
                        "eng_name": eng_name.strip()
                    })
    except Exception as e:
        print(f"Error reading google sheet: {e}")
    return authors_info

def fetch_author_rag_data(author_info):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("Error: SERPAPI_KEY not found")
        return None

    author_id = author_info["id"]
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

    author_profile = results.get("author", {})
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
        "th_nm": author_info["thai_name"],
        "en_nm": author_info["eng_name"] or author_profile.get("name", ""),
        "aff": author_profile.get("affiliations", ""),
        "int": [i.get("title", "") for i in author_profile.get("interests", [])],
        "cite": cites,
        "h": h_idx
    }
    metadata = {k: v for k, v in metadata.items() if v}

    pubs = []
    for article in articles:
        pub = {
            "t": article.get("title", ""),
            "y": article.get("year", ""),
            "d": article.get("snippet", ""),  # เพิ่ม Description/Snippet ตรงนี้
            "c": article.get("cited_by", {}).get("value", 0),
            "u": article.get("link", "")
        }
        pub = {k: v for k, v in pub.items() if v}
        pubs.append(pub)

    return {"m": metadata, "p": pubs}

def main():
    authors_list = get_authors_from_sheet(SHEET_URL)
    print(f"Found authors from sheet: {len(authors_list)}")

    all_authors_data = []
    for author in authors_list:
        data = fetch_author_rag_data(author)
        if data:
            all_authors_data.append(data)
            print(f"Successfully fetched {author['id']}")
        else:
            print(f"Skipped ID: {author['id']}")

    if all_authors_data:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_authors_data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"Saved minified data to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
