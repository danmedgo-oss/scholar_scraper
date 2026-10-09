import os
import json
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

SHEET_URL = "https://docs.google.com/spreadsheets/d/12YLMeZbR_CEzCbmnLE7V0FuxffjhL2IUlteBCAXMEEM/export?format=csv"
OUTPUT_SCHOLAR = "scholar_data.json"
OUTPUT_THAIJO = "thaijo_data.json"

def get_authors_from_sheet(sheet_url):
    authors_info = []
    try:
        df = pd.read_csv(sheet_url)
        for _, row in df.iterrows():
            scholar_link = ""
            thaijo_link = ""
            
            # ดึงชื่อ
            thai_name = str(row.get("ชื่อ", "")) if pd.notna(row.get("ชื่อ", "")) else ""
            eng_name = str(row.get("Name", "")) if pd.notna(row.get("Name", "")) else ""
            
            # ค้นหาลิงก์ Scholar และ ThaiJO จากทุกคอลัมน์ หรือระบุเจาะจง
            if "Link Thaijo" in df.columns and pd.notna(row["Link Thaijo"]):
                thaijo_link = str(row["Link Thaijo"]).strip()

            for col in df.columns:
                val = str(row[col]).strip()
                if "scholar.google.com" in val:
                    scholar_link = val
                if not thaijo_link and "tci-thaijo.org" in val:
                    thaijo_link = val
            
            # ค้นหา ID ของ Google Scholar
            author_id = ""
            if scholar_link:
                match = re.search(r"user=([a-zA-Z0-9_-]+)", scholar_link)
                if match:
                    author_id = match.group(1)
            
            # เก็บข้อมูลถ้ามีลิงก์อย่างใดอย่างหนึ่ง
            if author_id or thaijo_link:
                authors_info.append({
                    "id": author_id,
                    "thai_name": thai_name.strip(),
                    "eng_name": eng_name.strip(),
                    "thaijo_link": thaijo_link
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
    print(f"[Scholar] Fetching data for ID: {author_id}")
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
            "d": article.get("snippet", ""),
            "c": article.get("cited_by", {}).get("value", 0),
            "u": article.get("link", "")
        }
        pub = {k: v for k, v in pub.items() if v}
        pubs.append(pub)

    return {"m": metadata, "p": pubs}

def fetch_thaijo_data(author_info):
    thaijo_url = author_info.get("thaijo_link")
    display_name = author_info['thai_name'] or author_info['eng_name'] or "Unknown"
    
    if not thaijo_url:
        return None
        
    print(f"[ThaiJO]  Fetching data for: {display_name}")
    
    try:
        # ยิง Request ไปดึงหน้าเว็บ TCI ThaiJO
        res = requests.get(thaijo_url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        articles = []
        # หาข้อมูลจาก class: obj_article_summary (มาตรฐานระบบ OJS/ThaiJO)
        for item in soup.find_all('div', class_='obj_article_summary'):
            title_tag = item.find(class_='title')
            authors_tag = item.find(class_='authors')
            date_tag = item.find(class_='published')
            
            if title_tag:
                title = title_tag.text.strip()
                url = title_tag.find('a')['href'] if title_tag.find('a') else ""
                authors = authors_tag.text.strip() if authors_tag else ""
                year = date_tag.text.strip().split('-')[0] if date_tag else ""
                
                pub = {
                    "t": title,
                    "y": year,
                    "a": authors,
                    "u": url
                }
                pub = {k: v for k, v in pub.items() if v}
                articles.append(pub)
                
        if articles:
            return {
                "name": display_name,
                "publications": articles
            }
            
    except Exception as e:
        print(f"Error scraping ThaiJO for {display_name}: {e}")
        
    return None

def main():
    authors_list = get_authors_from_sheet(SHEET_URL)
    print(f"Found authors from sheet: {len(authors_list)}")

    all_scholar_data = []
    all_thaijo_data = []
    
    for author in authors_list:
        # 1. ดึงข้อมูล Google Scholar
        if author.get("id"):
            s_data = fetch_author_rag_data(author)
            if s_data:
                all_scholar_data.append(s_data)
                print(f"  -> Successfully fetched Scholar ID: {author['id']}")
            else:
                print(f"  -> Skipped Scholar ID: {author['id']}")
                
        # 2. ดึงข้อมูล ThaiJO
        if author.get("thaijo_link"):
            t_data = fetch_thaijo_data(author)
            if t_data:
                all_thaijo_data.append(t_data)
                print(f"  -> Successfully fetched ThaiJO: {author['thai_name']}")
            else:
                print(f"  -> Skipped ThaiJO: {author['thai_name']}")
        
        print("-" * 30)

    # บันทึกไฟล์ที่ 1: scholar_data.json
    if all_scholar_data:
        with open(OUTPUT_SCHOLAR, "w", encoding="utf-8") as f:
            json.dump(all_scholar_data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"Saved minified Scholar data to {OUTPUT_SCHOLAR}")
        
    # บันทึกไฟล์ที่ 2: thaijo_data.json
    if all_thaijo_data:
        with open(OUTPUT_THAIJO, "w", encoding="utf-8") as f:
            json.dump(all_thaijo_data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"Saved minified ThaiJO data to {OUTPUT_THAIJO}")

if __name__ == "__main__":
    main()
