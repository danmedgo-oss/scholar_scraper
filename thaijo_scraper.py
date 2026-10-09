import os
import json
import pandas as pd
from serpapi import GoogleSearch

SHEET_URL = "https://docs.google.com/spreadsheets/d/12YLMeZbR_CEzCbmnLE7V0FuxffjhL2IUlteBCAXMEEM/export?format=csv"
OUTPUT_FILE = "thaijo_data.json"

def get_thaijo_from_sheet(sheet_url):
    authors_info = []
    try:
        df = pd.read_csv(sheet_url)
        for _, row in df.iterrows():
            thaijo_link = ""
            thai_name = str(row.get("ชื่อ", "")) if pd.notna(row.get("ชื่อ", "")) else ""
            eng_name = str(row.get("Name", "")) if pd.notna(row.get("Name", "")) else ""
            
            if "Link Thaijo" in df.columns and pd.notna(row["Link Thaijo"]):
                thaijo_link = str(row["Link Thaijo"]).strip()

            if not thaijo_link:
                for col in df.columns:
                    val = str(row[col]).strip()
                    if "tci-thaijo.org" in val:
                        thaijo_link = val
                        break
            
            if thaijo_link or thai_name:
                authors_info.append({
                    "thai_name": thai_name.strip(),
                    "eng_name": eng_name.strip()
                })
    except Exception as e:
        print(f"Error reading google sheet: {e}")
    return authors_info

def fetch_thaijo_data_via_google(author_info):
    api_key = os.getenv("SERPAPI_KEY")
    display_name = author_info['thai_name'] or author_info['eng_name']
    
    if not display_name:
        return None
        
    print(f"Fetching ThaiJO via Google for: {display_name}")
    
    if not api_key:
        print("Error: SERPAPI_KEY not found in environment!")
        return None
        
    try:
        params = {
            "engine": "google",
            "q": f'site:tci-thaijo.org "{display_name}"',
            "api_key": api_key,
            "num": 5
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        organic_results = results.get("organic_results", [])
        if not organic_results:
            return None
            
        articles = []
        for result in organic_results:
            title = result.get("title", "").replace(" - ThaiJO", "").strip()
            link = result.get("link", "")
            
            if "article/view" not in link:
                continue
                
            pub = {
                "t": title,
                "a": display_name,
                "u": link
            }
            articles.append(pub)
            
        if articles:
            return {
                "name": display_name,
                "publications": articles
            }
            
    except Exception as e:
        print(f"Error fetching ThaiJO via Google for {display_name}: {e}")
        
    return None

def main():
    authors_list = get_thaijo_from_sheet(SHEET_URL)
    print(f"Found authors from sheet: {len(authors_list)}")

    all_thaijo_data = []
    for author in authors_list:
        data = fetch_thaijo_data_via_google(author)
        if data:
            all_thaijo_data.append(data)
            print(f"Successfully fetched {author['thai_name']}")
        else:
            print(f"Skipped {author['thai_name']}")

    if all_thaijo_data:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_thaijo_data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"Saved minified data to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
