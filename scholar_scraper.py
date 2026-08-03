import os
import json
from datetime import datetime
from serpapi import GoogleSearch

AUTHOR_ID = "8UGgxCIAAAAJ"
OUTPUT_FILE = "scholar_data.json"

def fetch_author_rag_data(author_id):
    # ดึง API Key จาก GitHub Secrets
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("🚨 Error: ไม่พบ SERPAPI_KEY ใน Environment Variables")
        return None

    print(f"🚀 กำลังดึงข้อมูล Scholar ID: {author_id} ผ่าน SerpApi...")
    
    # กำหนดพารามิเตอร์สำหรับ SerpApi
    params = {
        "engine": "google_scholar_author",
        "author_id": author_id,
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ SerpApi: {e}")
        return None

    # ตรวจสอบว่ามีข้อมูลผู้แต่งหรือไม่
    if "author" not in results:
        print("⚠️ ไม่พบข้อมูลโปรไฟล์ กรุณาตรวจสอบ Author ID")
        return None

    author_info = results.get("author", {})
    articles = results.get("articles", [])

    print("✅ ดึงข้อมูลสำเร็จ! กำลังจัดรูปแบบสำหรับ RAG...")

    # 1. จัดเตรียม Metadata
    metadata = {
        "scholar_id": author_id,
        "name": author_info.get("name", ""),
        "affiliation": author_info.get("affiliations", ""),
        "interests": [interest.get("title", "") for interest in author_info.get("interests", [])],
        "total_citations": results.get("cited_by", {}).get("table", [{}])[0].get("citations", {}).get("all", 0),
        "h_index": results.get("cited_by", {}).get("table", [{}])[1].get("h_index", {}).get("all", 0),
        "last_updated": datetime.now().isoformat()
    }

    # 2. จัดเตรียม Document Chunks
    publications = []
    for article in articles:
        publications.append({
            "title": article.get("title", ""),
            "pub_year": article.get("year", "Unknown"),
            "citations": article.get("cited_by", {}).get("value", 0),
            "citation_url": article.get("link", "")
        })

    return {
        "metadata": metadata,
        "publications": publications
    }

def main():
    rag_data = fetch_author_rag_data(AUTHOR_ID)
    
    if rag_data:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(rag_data, f, ensure_ascii=False, indent=4)
        print(f"💾 บันทึกข้อมูลลงไฟล์ {OUTPUT_FILE} เรียบร้อยแล้ว พร้อมนำไปใส่ Vector Database!")
    else:
        print("❌ ยกเลิกการอัปเดตไฟล์ JSON")

if __name__ == "__main__":
    main()
