from utils.supabase_client import get_supabase

async def run(arac_bilgi: dict) -> dict:
    il = arac_bilgi.get("il","").strip()
    ilce = arac_bilgi.get("ilce","").strip()
    mahalle = arac_bilgi.get("mahalle","").strip()
    
    if not il:
        return {"success": False, "error": "Il bilgisi eksik", "istasyonlar": [], "harita_url": ""}
    
    db = get_supabase()
    
    try:
        # Once ilce bazli ara
        if ilce:
            q = db.table("stations").select("id,ad,franchise,il,ilce,adres,telefon,puan,sponsor_level,google_maps_url").eq("is_active", True).ilike("il", il).ilike("ilce", ilce).order("sponsor_level", desc=True).order("puan", desc=True).limit(6)
            result = q.execute()
            istasyonlar = result.data
        else:
            istasyonlar = []
        
        # Ilcede yoksa il bazli ara
        if not istasyonlar:
            q = db.table("stations").select("id,ad,franchise,il,ilce,adres,telefon,puan,sponsor_level,google_maps_url").eq("is_active", True).ilike("il", il).order("sponsor_level", desc=True).order("puan", desc=True).limit(6)
            result = q.execute()
            istasyonlar = result.data
        
        # Harita URL
        lokasyon = " ".join(filter(None, [mahalle, ilce, il]))
        harita_url = "https://maps.google.com/maps?q=" + "+".join(["oto+ekspertiz"] + lokasyon.split()) + "&output=embed&hl=tr"
        
        print(f"Agent3: {len(istasyonlar)} istasyon bulundu - {il}/{ilce}")
        return {
            "success": True,
            "istasyonlar": istasyonlar,
            "harita_url": harita_url,
            "lokasyon": lokasyon
        }
    except Exception as e:
        print(f"Agent3 hata: {e}")
        return {"success": False, "error": str(e), "istasyonlar": [], "harita_url": ""}
