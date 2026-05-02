"""
Referans Sistemi
3 arkadaş davet et → 3 ücretsiz analiz kazan
Davet edilen kişi de 1 ücretsiz analiz kazanır
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.supabase_client import get_supabase
import uuid, random, string

router = APIRouter()

def generate_referral_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.get("/{user_id}/code")
async def get_referral_code(user_id: str):
    """Kullanıcının referans kodunu getir veya oluştur"""
    db = get_supabase()
    user = db.table("users").select("referral_code, free_analyses").eq("id", user_id).execute()
    
    if not user.data:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    code = user.data[0].get("referral_code")
    if not code:
        code = generate_referral_code()
        db.table("users").update({"referral_code": code}).eq("id", user_id).execute()
    
    return {
        "referral_code": code,
        "share_url": f"https://ekspertizai.com?ref={code}",
        "share_text": f"Araç almadan önce ekspertiz raporunu EkspertizAI ile analiz et! İlk analizin ücretsiz. {code} kodunu kullan: https://ekspertizai.com?ref={code}",
        "free_analyses": user.data[0].get("free_analyses", 1)
    }

@router.post("/apply")
async def apply_referral(referred_user_id: str, referral_code: str):
    """
    Yeni kullanıcı referans kodu ile geldi.
    - Yeni kullanıcıya +1 ücretsiz analiz
    - Referans veren kişinin başarılı davet sayısını artır
    - 3 başarılı davette +3 ücretsiz analiz
    """
    db = get_supabase()
    
    # Referans kodunu bul
    referrer = db.table("users").select("id, referral_code, free_analyses")\
        .eq("referral_code", referral_code).execute()
    
    if not referrer.data:
        raise HTTPException(status_code=404, detail="Geçersiz referans kodu")
    
    referrer_id = referrer.data[0]["id"]
    
    if referrer_id == referred_user_id:
        raise HTTPException(status_code=400, detail="Kendi referans kodunuzu kullanamazsınız")
    
    # Daha önce bu referans kullanıldı mı?
    existing = db.table("referrals").select("id")\
        .eq("referrer_id", referrer_id)\
        .eq("referred_user_id", referred_user_id).execute()
    if existing.data:
        return {"message": "Referans zaten uygulandı"}
    
    # Referans kaydını oluştur
    db.table("referrals").insert({
        "id": str(uuid.uuid4()),
        "referrer_id": referrer_id,
        "referred_user_id": referred_user_id,
        "status": "completed",
        "bonus_given": False
    }).execute()
    
    # Davet edilen kişiye +1 analiz
    referred = db.table("users").select("free_analyses").eq("id", referred_user_id).execute()
    new_free = referred.data[0].get("free_analyses", 1) + 1
    db.table("users").update({"free_analyses": new_free}).eq("id", referred_user_id).execute()
    
    # Referans verenin tamamlanan davet sayısını kontrol et
    completed = db.table("referrals").select("id")\
        .eq("referrer_id", referrer_id)\
        .eq("status", "completed")\
        .eq("bonus_given", False).execute()
    
    # Her 3 davette +3 analiz
    if len(completed.data) >= 3:
        referrer_free = referrer.data[0].get("free_analyses", 1) + 3
        db.table("users").update({"free_analyses": referrer_free}).eq("id", referrer_id).execute()
        # Bonus verildi olarak işaretle
        ids = [r["id"] for r in completed.data[:3]]
        for rid in ids:
            db.table("referrals").update({"bonus_given": True}).eq("id", rid).execute()
    
    return {"success": True, "message": "Referans uygulandı! 1 ücretsiz analiz hakkı kazandınız."}

@router.get("/{user_id}/stats")
async def get_referral_stats(user_id: str):
    """Kullanıcının referans istatistikleri"""
    db = get_supabase()
    referrals = db.table("referrals").select("status, bonus_given")\
        .eq("referrer_id", user_id).execute()
    
    total = len(referrals.data)
    bonus_given = sum(1 for r in referrals.data if r.get("bonus_given"))
    next_bonus_at = 3 - (total % 3) if total % 3 != 0 else 3
    
    return {
        "total_referrals": total,
        "bonus_earned_count": bonus_given // 3 if bonus_given else 0,
        "next_bonus_in": next_bonus_at
    }
