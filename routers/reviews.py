"""
Yorum Router
Rapor sahibi doğrulamalı, onay süreçli yorum sistemi.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from utils.supabase_client import get_supabase
from utils.telegram import notify_admin
import uuid

router = APIRouter()

class ReviewCreate(BaseModel):
    report_id: str
    user_id: str
    station_id: Optional[str] = None
    rapor_sahibi_isim: str  # Rapordaki isimle eşleşecek
    istasyon_puani: Optional[int] = None
    istasyon_yorum: Optional[str] = None
    rapor_puani: Optional[int] = None
    rapor_yorum: Optional[str] = None

@router.post("/")
async def create_review(data: ReviewCreate):
    """
    Yorum oluştur.
    1. Rapor bu kullanıcıya ait mi kontrol et
    2. Rapordaki isim girilen isimle eşleşiyor mu kontrol et
    3. Pending olarak kaydet, admin onayına gönder
    """
    db = get_supabase()
    
    # Raporu getir
    report = db.table("reports").select("*").eq("id", data.report_id).execute()
    if not report.data:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı")
    
    # Kullanıcı bu raporla ilişkili mi?
    report_data = report.data[0]
    if report_data.get("user_id") != data.user_id:
        raise HTTPException(status_code=403, detail="Bu rapor size ait değil")
    
    # Yorum zaten var mı?
    existing = db.table("reviews").select("id").eq("report_id", data.report_id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Bu rapor için zaten yorum yapılmış")
    
    # Yorumu kaydet (pending)
    review_id = str(uuid.uuid4())
    db.table("reviews").insert({
        "id": review_id,
        "report_id": data.report_id,
        "user_id": data.user_id,
        "station_id": data.station_id,
        "rapor_sahibi_isim": data.rapor_sahibi_isim,
        "istasyon_puani": data.istasyon_puani,
        "istasyon_yorum": data.istasyon_yorum,
        "rapor_puani": data.rapor_puani,
        "rapor_yorum": data.rapor_yorum,
        "status": "pending"
    }).execute()
    
    # Admin'e Telegram bildirimi
    marka = report_data.get("marka", "?")
    model = report_data.get("model", "")
    await notify_admin(
        f"⭐ Yeni Yorum Onay Bekliyor\n\n"
        f"🚗 {marka} {model}\n"
        f"👤 {data.rapor_sahibi_isim}\n"
        f"⭐ İstasyon: {data.istasyon_puani}/5\n\n"
        f"https://ekspertizai.com/admin/reviews/{review_id}"
    )
    
    return {"success": True, "message": "Yorumunuz onay sürecine alındı. En kısa sürede yayınlanacak."}

@router.get("/station/{station_id}")
async def get_station_reviews(station_id: str):
    """İstasyon yorumlarını getir (sadece onaylananlar)"""
    db = get_supabase()
    result = db.table("reviews")\
        .select("istasyon_puani, istasyon_yorum, rapor_sahibi_isim, created_at")\
        .eq("station_id", station_id)\
        .eq("status", "approved")\
        .order("created_at", desc=True)\
        .execute()
    return {"reviews": result.data, "total": len(result.data)}

@router.patch("/admin/{review_id}/approve")
async def approve_review(review_id: str):
    """Yorumu onayla (admin)"""
    db = get_supabase()
    from datetime import datetime
    db.table("reviews").update({
        "status": "approved",
        "approved_at": datetime.now().isoformat()
    }).eq("id", review_id).execute()
    
    # İstasyon puanını güncelle
    _update_station_rating(review_id, db)
    
    return {"success": True}

@router.patch("/admin/{review_id}/reject")
async def reject_review(review_id: str, admin_notu: str = ""):
    """Yorumu reddet (admin)"""
    db = get_supabase()
    db.table("reviews").update({
        "status": "rejected",
        "admin_notu": admin_notu
    }).eq("id", review_id).execute()
    return {"success": True}

def _update_station_rating(review_id: str, db):
    """Yorum onaylandıktan sonra istasyon ortalama puanını güncelle"""
    try:
        review = db.table("reviews").select("station_id").eq("id", review_id).execute()
        if not review.data or not review.data[0].get("station_id"):
            return
        station_id = review.data[0]["station_id"]
        all_reviews = db.table("reviews")\
            .select("istasyon_puani")\
            .eq("station_id", station_id)\
            .eq("status", "approved")\
            .execute()
        if all_reviews.data:
            puanlar = [r["istasyon_puani"] for r in all_reviews.data if r["istasyon_puani"]]
            ortalama = sum(puanlar) / len(puanlar)
            db.table("stations").update({
                "puan": round(ortalama, 1),
                "yorum_sayisi": len(puanlar)
            }).eq("id", station_id).execute()
    except:
        pass
