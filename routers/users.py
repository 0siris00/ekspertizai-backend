from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import random, string
from utils.supabase_client import get_supabase

router = APIRouter()

class UserCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    referral_code: Optional[str] = None
    password: Optional[str] = None

@router.post("/users/register")
async def register_user(data: UserCreate):
    db = get_supabase()
    existing = db.table("users").select("id").eq("phone", data.phone).execute()
    if existing.data:
        return {"exists": True, "user_id": existing.data[0]["id"]}
    ref_code = "EKS-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    referrer_id = None
    if data.referral_code:
        ref = db.table("users").select("id").eq("referral_code", data.referral_code).execute()
        if ref.data:
            referrer_id = ref.data[0]["id"]
    user = {
        "phone": data.phone,
        "name": data.name,
        "referral_code": ref_code,
        "referred_by": referrer_id,
        "free_analyses": 1,
        "total_analyses": 0,
        "invite_count": 0,
        "password": data.password,
        "created_at": datetime.now().isoformat()
    }
    result = db.table("users").insert(user).execute()
    user_id = result.data[0]["id"]
    if referrer_id:
        referrer = db.table("users").select("invite_count").eq("id", referrer_id).execute()
        if referrer.data:
            new_count = referrer.data[0].get("invite_count", 0) + 1
            db.table("users").update({"invite_count": new_count}).eq("id", referrer_id).execute()
            if new_count % 3 == 0:
                prize = random.choice(["free_analysis", "expert_call"])
                db.table("prizes").insert({"user_id": referrer_id, "type": prize, "status": "active", "reason": "referral_reward", "created_at": datetime.now().isoformat()}).execute()
    return {"exists": False, "user_id": user_id, "referral_code": ref_code}

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    db = get_supabase()
    result = db.table("users").select("*").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return result.data[0]

@router.get("/users/{user_id}/analyses-remaining")
async def get_analyses_remaining(user_id: str):
    db = get_supabase()
    result = db.table("users").select("free_analyses").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return {"free_analyses": result.data[0].get("free_analyses", 0)}

@router.post("/users/{user_id}/use-analysis")
async def use_analysis(user_id: str):
    db = get_supabase()
    user = db.table("users").select("free_analyses,total_analyses").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    free = user.data[0].get("free_analyses", 0)
    if free <= 0:
        raise HTTPException(status_code=402, detail="Analiz hakkı kalmadı")
    db.table("users").update({"free_analyses": free - 1, "total_analyses": user.data[0].get("total_analyses", 0) + 1}).eq("id", user_id).execute()
    return {"success": True, "remaining": free - 1}

class UserLogin(BaseModel):
    phone: str
    password: str

@router.post("/users/login")
async def login_user(data: UserLogin):
    db = get_supabase()
    result = db.table("users").select("*").eq("phone", data.phone).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Telefon veya şifre hatalı")
    user = result.data[0]
    if user.get("password") != data.password:
        raise HTTPException(status_code=401, detail="Telefon veya şifre hatalı")
    return {"user_id": user["id"], "name": user.get("name",""), "referral_code": user.get("referral_code","")}
