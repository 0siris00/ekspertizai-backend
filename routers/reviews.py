from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import random
from utils.supabase_client import get_supabase

router = APIRouter()

class ReviewCreate(BaseModel):
    user_id: str
    station_id: Optional[str] = None
    station_name: str
    report_id: Optional[str] = None
    rating: int
    comment: str

@router.post("/reviews")
async def create_review(data: ReviewCreate):
    if not 1 <= data.rating <= 5:
        raise HTTPException(status_code=400, detail="Puan 1-5 arası olmalı")
    db = get_supabase()
    review = {
        "user_id": data.user_id,
        "station_id": data.station_id,
        "station_name": data.station_name,
        "report_id": data.report_id,
        "rating": data.rating,
        "comment": data.comment,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    db.table("reviews").insert(review).execute()
    if random.random() < 0.3:
        prize = random.choice(["free_analysis", "expert_call"])
        db.table("prizes").insert({
            "user_id": data.user_id,
            "type": prize,
            "status": "active",
            "reason": "review_reward",
            "created_at": datetime.now().isoformat()
        }).execute()
        return {"success": True, "prize": prize, "message": "Yorumunuz için teşekkürler! Ödül kazandınız."}
    return {"success": True, "message": "Yorumunuz onay bekliyor."}

@router.get("/reviews/station/{station_name}")
async def get_station_reviews(station_name: str):
    db = get_supabase()
    result = db.table("reviews").select("*").eq("station_name", station_name).eq("status", "approved").order("created_at", desc=True).execute()
    return {"reviews": result.data}
