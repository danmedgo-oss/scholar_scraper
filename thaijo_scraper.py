import os
import json
import pandas as pd
import requests
import re
import urllib.parse
import time
from bs4 import BeautifulSoup

SHEET_URL = "https://docs.google.com/spreadsheets/d/12YLMeZbR_CEzCbmnLE7V0FuxffjhL2IUlteBCAXMEEM/export?format=csv"
OUTPUT_FILE = "thaijo_data.json"

def get_junk_links():
    """ดึงลิงก์บทความแนะนำใน Sidebar ออกมาก่อน เพื่อเอาไว้กรองทิ้ง"""
    try:
        url = 'https://www.tci-thaijo.org/en/articles?q="NOBODY_MATCH_12345"'
        r = requests.get(url, timeout=15)
        # Regex หารูปแบบลิงก์บทความ (รองรับทั้งแบบปกติและแบบที่มี \/ ในโค้ดของ Nuxt)
        links = re.findall(r'https:(?:\\/\\/|//)he\d+\.tci-thaijo\.org(?:\\/|/)index\.php(?:\\/|/)[a-zA-Z0-9_]+(?:\\/|/)article(?:\\/|/)view(?:\\/|/)\d+', r.text)
        return set([link.replace('\\/', '/') for link in links])
    except:
        return set()

def get_thaijo_from_sheet(sheet_url):
    authors_info = []
    try:
        df = pd.read_csv(sheet_url)
        for _, row in df.iterrows():
            thai_name = str(row.get("ชื่อ", "")) if pd.notna(row.get("ชื่อ", "")) else ""
            eng_name = str(row.get("Name", "")) if pd.notna(row.get("Name", "")) else ""
            if thai_name or eng_name:
                authors_info.append({"thai_name": thai_name.strip(), "eng_name": eng_name.strip()})
    except Exception as e:
        print(f"Error: {e}")
    return authors_info

def fetch_article_title(url):
    """เข้าไปที่หน้าบทความเพื่อดึงชื่อเรื่องที่ถูกต้อง"""
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.text if soup.title else ""
        title = title.split("|")[0].strip() # ตัดคำว่า | NU Journal of ... ทิ้ง
        return title if title else "งานวิจัยบน ThaiJO (ไม่สามารถดึงชื่อเรื่องได้)"
    except:
        return "งานวิจัยบน ThaiJO"

def main():
    junk_links = get_junk_links()
    print(f"Found {len(junk_links)} junk sidebar links to ignore.")
    
    authors_list = get_thaijo_from_sheet(SHEET_URL)
    all_thaijo_data = []
    
    for author in authors_list:
        display_name = author['thai_name'] or author['eng_name']
        if not display_name: continue
        
        try:
            print(f"Fetching ThaiJO directly for: {display_name}...")
            query = urllib.parse.quote(f'"{display_name}"')
            url = f"https://www.tci-thaijo.org/en/articles?q={query}"
            r = requests.get(url, timeout=15)
            
            raw_links = re.findall(r'https:(?:\\/\\/|//)he\d+\.tci-thaijo\.org(?:\\/|/)index\.php(?:\\/|/)[a-zA-Z0-9_]+(?:\\/|/)article(?:\\/|/)view(?:\\/|/)\d+', r.text)
            all_links = set([link.replace('\\/', '/') for link in raw_links])
            
            # ลบลิงก์ขยะออก จะเหลือแต่ลิงก์งานวิจัยของคนๆ นี้จริงๆ
            real_links = list(all_links - junk_links)
            
            if real_links:
                articles = []
                # ดึงแค่ 5 เรื่องแรกเพื่อไม่ให้บอททำงานนานเกินไป
                for link in real_links[:5]:
                    title = fetch_article_title(link)
                    articles.append({
                        "t": title,
                        "a": display_name,
                        "u": link
                    })
                
                all_thaijo_data.append({
                    "name": display_name,
                    "publications": articles
                })
                print(f" -> Found {len(real_links)} articles")
            else:
                print(" -> No articles found")
                
        except Exception as e:
            print(f" -> Error: {e}")
            
        time.sleep(1) # หน่วงเวลา 1 วินาที เพื่อไม่ให้เซิร์ฟเวอร์ ThaiJO บล็อคเรา
        
    if all_thaijo_data:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_thaijo_data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"Saved directly scraped data to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
