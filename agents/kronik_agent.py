import anthropic
import os
from utils.supabase_client import get_supabase

async def get_kronik_sorunlar(marka: str, model: str, yil: int) -> list:
    if not marka or not model:
        return []
    db = get_supabase()
    try:
        result = db.table("kronik_sorunlar").select("*").ilike("marka", marka).ilike("model", model).execute()
        if result.data:
            return result.data[0].get("sorunlar", [])
    except:
        pass
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=800,
            messages=[{"role":"user","content":f"{yil} model {marka} {model} aracinin Turkiye piyasasinda bilinen kronik sorunlari ve yaygin arizalari nelerdir? Maksimum 8 madde, sade Turkce, her biri 1 cumle. Sadece maddeleri yaz, baska bir sey yazma."}]
        )
        text = resp.content[0].text
        sorunlar = [l.strip().lstrip("-*123456789. ").strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 10][:8]
        if sorunlar:
            try:
                db.table("kronik_sorunlar").insert({"marka":marka.upper(),"model":model.upper(),"yil_baslangic":yil-2,"yil_bitis":yil+2,"sorunlar":sorunlar}).execute()
            except Exception as e:
                print("DB kayit:", e)
        return sorunlar
    except Exception as e:
        print(f"Kronik hata: {e}")
        return []
