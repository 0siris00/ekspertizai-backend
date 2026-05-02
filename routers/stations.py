from fastapi import APIRouter
from typing import Optional
router = APIRouter()

@router.get("/nearby")
async def get_nearby_stations(il: str, ilce: Optional[str] = None, limit: int = 5):
    return {"il": il, "ilce": ilce, "istasyonlar": [], "toplam": 0}

@router.get("/search")
async def search_stations(q: str, il: Optional[str] = None):
    return {"istasyonlar": [], "toplam": 0}
