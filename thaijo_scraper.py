import os
import json
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

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
            
            if thaijo_link:
                authors_info.append({
                    "thai_name": thai_name.strip(),
                    "eng_name": eng_name.strip(),
                    "thaijo_link": thaijo_link
                })
    except Exception as e:
        print(f"Error reading google sheet: {e}")
    return authors_info

def fetch_thaijo_data(author_info):
    thaijo_url = author_info.get("thaijo_link")
    display_name = author_info['thai_name'] or author_info['eng_name'] or "Unknown"
    
    print(f"Fetching ThaiJO data for: {display_name}")
    
    try:
        res = requests.get(thaijo_url, timeout=15)
        html_text = res.text.replace('\\u002F', '/').replace('\\/', '/')
        
        raw_links = re.findall(r'https://he\d+\.tci-thaijo\.org/index\.php/[a-zA-Z0-9_]+/article/view/\d+', html_text)
        clean_links = list(set(raw_links))
        
        articles = []
        for link in clean_links[:5]:
            try:
                page_res = requests.get(link, timeout=10)
                page_soup = BeautifulSoup(page_res.text, 'html.parser')
                
                title_tag = page_soup.find('h1', class_='page_title')
                if not title_tag: continue
                title = title_tag.text.strip()
                
                authors = []
                for author_span in page_soup.find_all('span', class_='name'):
                    authors.append(author_span.text.strip())
                authors_str = ", ".join(authors) if authors else ""
                
                year = ""
                date_div = page_soup.find('div', class_='item published')
                if date_div:
                    val_div = date_div.find('div', class_='value')
                    if val_div:
                        year_match = re.search(r'\b(20\d{2})\b', val_div.text)
                        if year_match: year = year_match.group(1)
                
                pub = {"t": title, "y": year, "a": authors_str, "u": link}
                pub = {k: v for k, v in pub.items() if v}
                articles.append(pub)
            except Exception as e:
                print(f"Error fetching article {link}: {e}")
                
        if articles:
            return {"name": display_name, "publications": articles}
            
    except Exception as e:
        print(f"Error scraping ThaiJO for {display_name}: {e}")
        
    return None

def main():
    authors_list = get_thaijo_from_sheet(SHEET_URL)
    print(f"Found ThaiJO authors from sheet: {len(authors_list)}")

    all_thaijo_data = []
    for author in authors_list:
        data = fetch_thaijo_data(author)
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
