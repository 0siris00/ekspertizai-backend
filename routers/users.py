"""
Kullanıcı Router
Kayıt, OTP doğrulama, kimlik yönetimi.
Hesap açma yok — isim/soyisim/telefon + OTP yeterli.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.otp import send_otp, verify_otp
from utils.supabase_client import get_supabase
import uuid

router = APIRouter()

class RegisterRequest(BaseModel):
    isim: str
    soyisim: str
    telefon: str  # 905XXXXXXXXX formatında
    kvkk_onay: bool

class OTPVerifyRequest(BaseModel):
    telefon: str
    kod: str

class OTPSendRequest(BaseModel):
    telefon: str

@router.post("/otp/send")
async def send_otp_endpoint(data: OTPSendRequest):
    """OTP gönder"""
    if not data.telefon.startswith("90") or len(data.telefon) != 12:
        raise HTTPException(status_code=400, detail="Telefon 90XXXXXXXXXX formatında olmalı")
    result = await send_otp(data.telefon)
    if not result["success"]:
        raise HTTPException(status_code=500, detail="OTP gönderilemedi")
    return {"message": "Doğrulama kodu gönderildi", "channel": result["channel"]}

@router.post("/otp/verify")
async def verify_otp_endpoint(data: OTPVerifyRequest):
    """OTP doğrula ve kullanıcı session oluştur"""
    if not verify_otp(data.telefon, data.kod):
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş kod")
    
    db = get_supabase()
    # Kullanıcı var mı kontrol et
    result = db.table("users").select("*").eq("phone", data.telefon).execute()
    
    if result.data:
        user = result.data[0]
    else:
        # Yeni kullanıcı oluştur
        user_id = str(uuid.uuid4())
        db.table("users").insert({"id": user_id, "phone": data.telefon}).execute()
        user = {"id": user_id, "phone": data.telefon}
    
    return {"verified": True, "user_id": user["id"]}

@router.post("/register")
async def register(data: RegisterRequest):
    """Kullanıcı bilgilerini kaydet (OTP doğrulama sonrası)"""
    if not data.kvkk_onay:
        raise HTTPException(status_code=400, detail="KVKK onayı zorunludur")
    
    db = get_supabase()
    result = db.table("users").select("*").eq("phone", data.telefon).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Önce OTP doğrulaması yapın")
    
    from datetime import datetime
    db.table("users").update({
        "kvkk_approved": True,
        "kvkk_approved_at": datetime.now().isoformat()
    }).eq("phone", data.telefon).execute()
    
    return {"success": True, "message": "Kayıt tamamlandı"}
