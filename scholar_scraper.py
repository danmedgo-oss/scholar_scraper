import os
import json
from serpapi import GoogleSearch

# 1. ใส่ ID ของผู้แต่งที่ต้องการดึงข้อมูลเพิ่มใน List นี้ได้เลย
AUTHOR_IDS = [
    "8UGgxCIAAAAJ",
    # "ID_คนที่_2",
    # "ID_คนที่_3" 
]
OUTPUT_FILE = "scholar_data.json"

def fetch_author_rag_data(author_id):
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("🚨 Error: ไม่พบ SERPAPI_KEY")
        return None

    print(f"🚀 กำลังดึงข้อมูล Scholar ID: {author_id}...")
    params = {
        "engine": "google_scholar_author",
        "author_id": author_id,
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

    if "author" not in results:
        return None

    author_info = results.get("author", {})
    articles = results.get("articles", [])

    # คำนวณ h-index และ citations
    cites = 0
    h_idx = 0
    for row in results.get("cited_by", {}).get("table", []):
        if "citations" in row: cites = row.get("citations", {}).get("all", 0)
        elif "h_index" in row: h_idx = row.get("h_index", {}).get("all", 0)

    # 2. จัดรูปแบบ Metadata แบบประหยัด Token (ย่อชื่อ Key และตัดข้อมูลว่าง)
    metadata = {
        "id": author_id,
        "nm": author_info.get("name", ""),
        "aff": author_info.get("affiliations", ""),
        "int": [i.get("title", "") for i in author_info.get("interests", [])],
        "cite": cites,
        "h": h_idx
    }
    metadata = {k: v for k, v in metadata.items() if v} # ลบ Key ที่ไม่มีข้อมูล

    # 3. จัดรูปแบบ Publications (ย่อชื่อ Key)
    pubs = []
    for article in articles:
        pub = {
            "t": article.get("title", ""),
            "y": article.get("year", ""),
            "c": article.get("cited_by", {}).get("value", 0),
            "u": article.get("link", "")
        }
        pub = {k: v for k, v in pub.items() if v} # ลบ Key ที่ไม่มีข้อมูล
        pubs.append(pub)

    return {"m": metadata, "p": pubs}

def main():
    all_authors_data = []
    
    for uid in AUTHOR_IDS:
        data = fetch_author_rag_data(uid)
        if data:
            all_authors_data.append(data)
            print(f"✅ ดึงข้อมูล {uid} สำเร็จ!")
        else:
            print(f"⚠️ ข้าม ID: {uid}")

    if all_authors_data:
        # บันทึกเป็น Minified JSON (ประหยัด Token ที่สุด)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_authors_data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"💾 บันทึกข้อมูลแบบ Minified ลง {OUTPUT_FILE} เรียบร้อยแล้ว!")

if __name__ == "__main__":
    main()
