import json
import time
import random
from scholarly import scholarly

# 1. กำหนด ID ของอาจารย์ที่ต้องการดึงข้อมูล
# จาก URL: https://scholar.google.com/citations?hl=en&user=8UGgxCIAAAAJ
AUTHOR_ID = "8UGgxCIAAAAJ"

def fetch_and_save_data(author_id):
    print(f"กำลังดึงข้อมูลของ ID: {author_id} ...")
    
    try:
        # ใช้ search_author_id แทน search_author เพื่อความแม่นยำ 100%
        author = scholarly.search_author_id(author_id)
        
        # ดึงข้อมูลทั้งหมดที่จำเป็น
        author_data = scholarly.fill(author, sections=['basics', 'indices', 'publications'])
        
        # 2. จัดโครงสร้างข้อมูลใหม่ให้สะอาดขึ้น (เหมาะสำหรับ RAG)
        extracted_data = {
            "name": author_data.get("name"),
            "affiliation": author_data.get("affiliation"),
            "interests": author_data.get("interests", []),
            "total_citations": author_data.get("citedby", 0),
            "h_index": author_data.get("hindex", 0),
            "publications": []
        }
        
        # วนลูปดึงข้อมูลเปเปอร์ที่สำคัญ
        for pub in author_data.get("publications", []):
            pub_info = {
                "title": pub.get("bib", {}).get("title"),
                "year": pub.get("bib", {}).get("pub_year", "Unknown"),
                "citations": pub.get("num_citations", 0)
            }
            extracted_data["publications"].append(pub_info)
            
        # 3. บันทึกข้อมูลลงไฟล์ JSON
        with open("scholar_data.json", "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
            
        print(f"✅ บันทึกข้อมูลของ {author_data['name']} สำเร็จ! (ได้ผลงาน {len(extracted_data['publications'])} ชิ้น)")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    fetch_and_save_data(AUTHOR_ID)
