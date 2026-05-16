import anthropic
import os
import json
from utils.supabase_client import get_supabase

def get_km_aralik(km: int) -> str:
    if not km: return "bilinmiyor"
    if km < 50000: return "0-50000"
    if km < 100000: return "50000-100000"
    if km < 150000: return "100000-150000"
    if km < 200000: return "150000-200000"
    return "200000+"

async def run(arac_bilgi: dict) -> dict:
    marka = arac_bilgi.get("marka","").strip().upper()
    model = arac_bilgi.get("model","").strip().upper()
    seri = arac_bilgi.get("seri","").strip().upper()
    yil = arac_bilgi.get("yil") or 0
    km = arac_bilgi.get("km") or 0
    km_aralik = get_km_aralik(km)
    
    if not marka or not model:
        return {"success": False, "error": "Marka/model eksik", "sorunlar": []}
    
    db = get_supabase()
    
    # Cache kontrolu
    try:
        q = db.table("sorgulanan_araclar").select("*").eq("marka", marka).eq("model", model)
        if yil: q = q.eq("yil", yil)
        q = q.eq("km_aralik", km_aralik)
        result = q.execute()
        if result.data:
            print(f"Agent2: Cache hit - {marka} {model} {yil}")
            return {"success": True, "sorunlar": result.data[0].get("kronik_sorunlar", []), "kaynak": "cache"}
    except Exception as e:
        print(f"Agent2 cache hata: {e}")
    
    # Web arastirma
    print(f"Agent2: Web arastirma - {marka} {seri} {model} {yil} {km_aralik}km")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    arac_tanim = f"{yil} {marka} {seri} {model}".strip()
    prompt = f"""{arac_tanim} ({km_aralik} km) aracinin Turkiye piyasasinda bilinen kronik sorunlari ve yaygin arizalari nelerdir?
Bu km araliginda ozellikle dikkat edilmesi gerekenler neler?
Maksimum 10 madde, sade Turkce, herkesin anlayacagi dilde, her madde 1-2 cumle.
Sadece maddeleri yaz, numara veya tire ile basla."""
    
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5", max_tokens=1000,
            messages=[{"role":"user","content":prompt}]
        )
        text = resp.content[0].text
        sorunlar = [l.strip().lstrip("-*0123456789. ").strip() 
                   for l in text.split("\n") 
                   if l.strip() and len(l.strip()) > 15][:10]
        
        # DB ye kaydet
        try:
            db.table("sorgulanan_araclar").insert({
                "marka": marka, "seri": seri, "model": model,
                "yil": yil, "km_aralik": km_aralik,
                "kronik_sorunlar": sorunlar, "kaynak": "web"
            }).execute()
            print(f"Agent2: {marka} {model} {yil} kaydedildi")
        except Exception as e:
            print(f"Agent2 kayit hata: {e}")
        
        return {"success": True, "sorunlar": sorunlar, "kaynak": "web"}
    except Exception as e:
        print(f"Agent2 hata: {e}")
        return {"success": False, "error": str(e), "sorunlar": []}
