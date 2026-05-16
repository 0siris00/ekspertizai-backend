import anthropic
import os
import json
import re
import base64
import fitz
from pathlib import Path
from utils.supabase_client import get_supabase

FIELDS = ["il","ilce","mahalle","marka","seri","model","yil","yakit_tipi","vites","km",
          "kasa_tipi","motor_gucu","motor_hacmi","cekis","agir_hasar_kayitli",
          "plaka_uyruk","aciklama","boya_degisen","tramer_durumu"]

PROMPT = """Bu arac ilan fotografindaki TUM bilgileri oku ve SADECE asagidaki JSON formatinda ver, baska hicbir sey yazma:
{"il":"","ilce":"","mahalle":"","marka":"","seri":"","model":"","yil":0,"yakit_tipi":"","vites":"","km":0,"kasa_tipi":"","motor_gucu":"","motor_hacmi":"","cekis":"","agir_hasar_kayitli":false,"plaka_uyruk":"","aciklama":"","boya_degisen":"","tramer_durumu":""}"""

async def run(file_path: str, report_id: str = None, user_id: str = None) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    ext = Path(file_path).suffix.lower()
    
    try:
        if ext == ".pdf":
            doc = fitz.open(file_path)
            text = "".join([page.get_text() for page in doc])
            doc.close()
            if len(text.strip()) > 100:
                resp = client.messages.create(
                    model="claude-haiku-4-5", max_tokens=800,
                    messages=[{"role":"user","content": PROMPT + "\n\nIlan metni:\n" + text[:3000]}]
                )
            else:
                doc2 = fitz.open(file_path)
                pix = doc2[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5))
                img_bytes = pix.tobytes("jpeg")
                doc2.close()
                if len(img_bytes) > 4*1024*1024:
                    doc3 = fitz.open(file_path)
                    pix = doc3[0].get_pixmap(matrix=fitz.Matrix(1,1))
                    img_bytes = pix.tobytes("jpeg")
                    doc3.close()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                resp = client.messages.create(
                    model="claude-haiku-4-5", max_tokens=800,
                    messages=[{"role":"user","content":[
                        {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":img_b64}},
                        {"type":"text","text":PROMPT}
                    ]}]
                )
        else:
            with open(file_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            media_type = "image/jpeg" if ext in [".jpg",".jpeg"] else "image/png"
            resp = client.messages.create(
                model="claude-haiku-4-5", max_tokens=800,
                messages=[{"role":"user","content":[
                    {"type":"image","source":{"type":"base64","media_type":media_type,"data":img_b64}},
                    {"type":"text","text":PROMPT}
                ]}]
            )
        
        raw = re.sub(r"```json|```","",resp.content[0].text.strip()).strip()
        info = json.loads(raw)
        
        for key in ["marka","seri","model","il","ilce","mahalle"]:
            if info.get(key): info[key] = str(info[key]).strip().upper()
        for key in ["yil","km"]:
            if info.get(key):
                try: info[key] = int(str(info[key]).replace(".","").replace(",",""))
                except: info[key] = 0
        
        db = get_supabase()
        record = {k: info.get(k) for k in FIELDS}
        record["report_id"] = report_id
        record["user_id"] = user_id
        result = db.table("arac_bilgileri").insert(record).execute()
        info["arac_bilgi_id"] = result.data[0]["id"] if result.data else None
        
        print(f"Agent1: {info.get('marka')} {info.get('seri')} {info.get('model')} {info.get('yil')} - {info.get('il')}/{info.get('ilce')}")
        return {"success": True, "data": info}
        
    except Exception as e:
        print(f"Agent1 hata: {e}")
        return {"success": False, "error": str(e), "data": {}}
