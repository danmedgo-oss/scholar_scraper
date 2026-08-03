import json
import sys
from scholarly import scholarly, ProxyGenerator

def main():
    print("กำลังค้นหา Free Proxy... (ขั้นตอนนี้อาจใช้เวลา 2-5 นาที)")
    
    # สร้างตัวจัดการ Proxy
    pg = ProxyGenerator()
    
    # ค้นหาและตั้งค่า Free Proxy
    # ข้อควรระวัง: บางครั้งอาจหา Proxy ฟรีที่ไม่โดนแบนไม่ได้เลย
    success = pg.FreeProxies() 
    
    if success:
        print("✅ ตั้งค่า Proxy สำเร็จ! ระบบกำลังเริ่มดึงข้อมูล...")
        scholarly.use_proxy(pg)
    else:
        print("⚠️ ไม่พบ Free Proxy ที่ใช้งานได้ในขณะนี้ สคริปต์จะลองดึงข้อมูลโดยไม่ใช้ Proxy (มีความเสี่ยงที่จะโดนบล็อกสูง)")

    try:
        author_name = 'Roongtiva Boonpracom'
        print(f"กำลังค้นหาโปรไฟล์ของ: {author_name}...")
        
        # ค้นหาชื่ออาจารย์
        search_query = scholarly.search_author(author_name)
        author = next(search_query)
        
        print("พบบัญชีผู้ใช้แล้ว! กำลังดึงรายละเอียดเชิงลึกและผลงานตีพิมพ์ทั้งหมด...")
        # ดึงข้อมูลทั้งหมดของโปรไฟล์ (ขั้นตอนนี้อาจใช้เวลานานขึ้นอยู่กับจำนวนเปเปอร์)
        author = scholarly.fill(author)
        
        # จัดโครงสร้างข้อมูลใหม่ให้สะอาดและเหมาะสำหรับ RAG (JSON Format)
        scholar_data = {
            "name": author.get("name", ""),
            "affiliation": author.get("affiliation", ""),
            "interests": author.get("interests", []),
            "total_citations": author.get("citedby", 0),
            "publications": []
        }
        
        # วนลูปเก็บข้อมูลเปเปอร์แต่ละชิ้น
        print("กำลังรวบรวมข้อมูลผลงานวิชาการ...")
        for pub in author.get("publications", []):
            pub_data = {
                "title": pub.get("bib", {}).get("title", ""),
                "year": pub.get("bib", {}).get("pub_year", "N/A"),
                "citations": pub.get("num_citations", 0)
            }
            scholar_data["publications"].append(pub_data)
            
        # บันทึกข้อมูลลงไฟล์ JSON
        output_filename = "scholar_data.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(scholar_data, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 สำเร็จ! บันทึกข้อมูลลงไฟล์ {output_filename} เรียบร้อยแล้ว")
        print(f"ดึงข้อมูลเปเปอร์มาได้ทั้งหมด {len(scholar_data['publications'])} รายการ")

    except StopIteration:
        print(f"❌ ข้อผิดพลาด: ไม่พบโปรไฟล์ที่ชื่อ '{author_name}' บน Google Scholar")
        sys.exit(1)
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดระหว่างดึงข้อมูล: {e}")
        print("หาก Error เกี่ยวข้องกับ Connection หรือ Max Tries แสดงว่า Proxy ที่ได้มาถูก Google บล็อกไปแล้วครับ")
        sys.exit(1)

if __name__ == "__main__":
    main()
