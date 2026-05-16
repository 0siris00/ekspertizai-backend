import anthropic
import os
import json
from utils.supabase_client import get_supabase

async def get_kronik_sorunlar(marka: str, model: str, yil: int = 2015, motor_hacmi: str = None, beygir: int = None) -> list:
    if not marka or not model:
        return []
    
    db = get_supabase()
    
    # Önce tam eşleşme ara (marka + model + motor + beygir)
    try:
        query = db.table("kronik_sorunlar").select("*").ilike("marka", marka).ilike("model", model)
        if motor_hacmi:
            query = query.eq("motor_hacmi", motor_hacmi)
        if beygir:
            query = query.eq("beygir", beygir)
        result = query.execute()
        if result.data:
            print(f"Kronik DB'den geldi: {marka} {model}")
            return result.data[0].get("sorunlar", [])
    except Exception as e:
        print(f"DB sorgu hatası: {e}")
    
    # Tam eşleşme yoksa sadece marka+model ara
    try:
        result2 = db.table("kronik_sorunlar").select("*").ilike("marka", marka).ilike("model", model).execute()
        if result2.data:
            print(f"Kronik DB'den (genel) geldi: {marka} {model}")
            return result2.data[0].get("sorunlar", [])
    except:
        pass
    
    # DB'de yoksa AI ile araştır
    print(f"Kronik AI ile araştırılıyor: {marka} {model} {motor_hacmi}")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    motor_info = f"{motor_hacmi}" if motor_hacmi else ""
    if beygir: motor_info += f" {beygir}hp"
    
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=800,
            messages=[{"role":"user","content":f"{yil} model {marka} {model} {motor_info} aracinin Turkiye piyasasinda bilinen kronik sorunlari ve yaygin arizalari nelerdir? Maksimum 8 madde, sade Turkce, herkesin anlayacagi dilde, her biri 1 cumle. Sadece maddeleri yaz."}]
        )
        text = resp.content[0].text
        sorunlar = [l.strip().lstrip("-*123456789. ").strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 10][:8]
        
        if sorunlar:
            try:
                db.table("kronik_sorunlar").insert({
                    "marka": marka.upper(),
                    "model": model.upper(),
                    "yil_baslangic": yil - 2,
                    "yil_bitis": yil + 2,
                    "motor_hacmi": motor_hacmi,
                    "beygir": beygir,
                    "sorunlar": sorunlar
                }).execute()
                print(f"Kronik DB'ye kaydedildi: {marka} {model}")
            except Exception as e:
                print(f"Kronik kayıt hatası: {e}")
        
        return sorunlar
    except Exception as e:
        print(f"Kronik AI hatası: {e}")
        return []
