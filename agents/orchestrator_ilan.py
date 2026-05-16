import asyncio
import uuid
from utils.supabase_client import get_supabase

async def run(file_path: str, file_type: str, report_id: str, user_id: str) -> dict:
    job_id = str(uuid.uuid4())[:8]
    print(f"[{job_id}] Araç ilan analizi başlıyor...")
    
    db = get_supabase()
    result = {
        "success": False,
        "arac_bilgi": {},
        "kronik_sorunlar": [],
        "istasyonlar": [],
        "harita_url": "",
        "yorum": {},
        "report_id": report_id
    }
    
    # AGENT 1 — İlan oku
    print(f"[{job_id}] Agent1: İlan okunuyor...")
    from agents.agent1_ilan import run as agent1_run
    a1 = await agent1_run(file_path, report_id, user_id)
    
    if not a1.get("success") or not a1.get("data"):
        print(f"[{job_id}] Agent1 başarısız, yeniden deneniyor...")
        a1 = await agent1_run(file_path, report_id, user_id)
    
    arac_bilgi = a1.get("data", {})
    result["arac_bilgi"] = arac_bilgi
    
    # Orchestrator kontrolü — kritik alanlar eksik mi?
    eksik = []
    if not arac_bilgi.get("marka"): eksik.append("marka")
    if not arac_bilgi.get("model"): eksik.append("model")
    if not arac_bilgi.get("il"): eksik.append("il")
    
    if eksik:
        print(f"[{job_id}] Eksik alanlar: {eksik} — Agent1 tekrar çalıştırılıyor")
        a1_retry = await agent1_run(file_path, report_id, user_id)
        if a1_retry.get("success"):
            for k in eksik:
                if a1_retry["data"].get(k):
                    arac_bilgi[k] = a1_retry["data"][k]
    
    # AGENT 2, 3, 4 paralel çalıştır
    print(f"[{job_id}] Agent2+3+4 paralel başlıyor...")
    from agents.agent2_kronik import run as agent2_run
    from agents.agent3_istasyon import run as agent3_run
    from agents.agent4_yorum import run as agent4_run
    
    a2_task = agent2_run(arac_bilgi)
    a3_task = agent3_run(arac_bilgi)
    
    a2, a3 = await asyncio.gather(a2_task, a3_task, return_exceptions=True)
    
    kronik_sorunlar = []
    if isinstance(a2, dict) and a2.get("success"):
        kronik_sorunlar = a2.get("sorunlar", [])
    
    istasyonlar = []
    harita_url = ""
    if isinstance(a3, dict) and a3.get("success"):
        istasyonlar = a3.get("istasyonlar", [])
        harita_url = a3.get("harita_url", "")
    
    # Agent 4 — kronik sorunlarla birlikte yorum
    a4 = await agent4_run(arac_bilgi, kronik_sorunlar)
    
    yorum = {}
    if isinstance(a4, dict) and a4.get("success"):
        yorum = a4.get("data", {})
    
    result.update({
        "success": True,
        "arac_bilgi": arac_bilgi,
        "kronik_sorunlar": kronik_sorunlar,
        "istasyonlar": istasyonlar,
        "harita_url": harita_url,
        "yorum": yorum
    })
    
    # DB'ye final sonucu kaydet
    try:
        db.table("reports").update({
            "status": "completed",
            "result": result
        }).eq("id", report_id).execute()
        print(f"[{job_id}] Tamamlandı: {arac_bilgi.get('marka')} {arac_bilgi.get('model')}")
    except Exception as e:
        print(f"[{job_id}] DB kayıt hata: {e}")
    
    return result
