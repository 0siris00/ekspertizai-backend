import anthropic
import os
import json
import re
import base64
from pathlib import Path

async def extract_ilan_info(file_path: str, file_type: str = "image") -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        from agents.agent1_reader import extract_text_from_pdf
        text = extract_text_from_pdf(file_path)
        prompt = "Bu arac ilani metninden bilgileri cikar ve SADECE JSON don: " + text[:2000] + "\nJSON: {il, ilce, marka, model, yil, km, motor_hacmi, beygir, fiyat, vites, yakit}"
        resp = client.messages.create(model="claude-haiku-4-5", max_tokens=500,
            messages=[{"role":"user","content":prompt}])
        raw = resp.content[0].text.strip()
    else:
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        media_type = "image/jpeg" if ext in [".jpg",".jpeg"] else "image/png"
        resp = client.messages.create(model="claude-haiku-4-5", max_tokens=500,
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":media_type,"data":image_data}},
                {"type":"text","text":"Bu arac ilan fotografindaki bilgileri JSON olarak ver. Sadece JSON, baska hicbir sey yazma. Alanlar: il, ilce, marka, model, yil, km, motor_hacmi, beygir, fiyat, vites, yakit"}
            ]}])
        raw = resp.content[0].text.strip()

    try:
        raw = re.sub(r"```json|```", "", raw).strip()
        info = json.loads(raw)
        for key in ["marka","model","il","ilce"]:
            if info.get(key): info[key] = str(info[key]).strip().upper()
        for key in ["yil","km","beygir"]:
            if info.get(key):
                try: info[key] = int(str(info[key]).replace(".","").replace(",",""))
                except: info[key] = 0
        return info
    except Exception as e:
        print(f"Ilan parse hatasi: {e}, raw: {raw[:100]}")
        return {}

async def save_ilan_to_db(info: dict, report_id: str = None, user_id: str = None):
    from utils.supabase_client import get_supabase
    db = get_supabase()
    try:
        record = {
            "report_id": report_id, "user_id": user_id,
            "il": info.get("il"), "ilce": info.get("ilce"),
            "marka": info.get("marka"), "model": info.get("model"),
            "yil": info.get("yil"), "km": info.get("km"),
            "motor_hacmi": info.get("motor_hacmi"), "beygir": info.get("beygir"),
            "fiyat": info.get("fiyat"), "raw_text": str(info)
        }
        db.table("arac_ilanlar").insert(record).execute()
        print(f"Ilan kaydedildi: {info.get('marka')} {info.get('model')}")
    except Exception as e:
        print(f"DB kayit hatasi: {e}")
