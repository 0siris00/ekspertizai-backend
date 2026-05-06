from fastapi import APIRouter
from typing import Optional
from utils.supabase_client import get_supabase

router = APIRouter()

@router.get("/stations")
async def list_stations(il: Optional[str] = None, ilce: Optional[str] = None,
                         franchise: Optional[str] = None, sponsored_only: bool = False,
                         limit: int = 20):
    db = get_supabase()
    query = db.table("stations").select("*").eq("is_active", True).order("sponsor_level", desc=True).order("puan", desc=True).limit(limit)
    if il:
        query = query.eq("il", il)
    if ilce:
        query = query.eq("ilce", ilce)
    if franchise:
        query = query.eq("franchise", franchise)
    if sponsored_only:
        query = query.gt("sponsor_level", 0)
    result = query.execute()
    return {"stations": result.data, "count": len(result.data)}

@router.get("/stations/by-location")
async def stations_by_location(il: str, ilce: Optional[str] = None, limit: int = 6):
    db = get_supabase()
    query = db.table("stations").select("id,ad,franchise,il,ilce,adres,telefon,google_maps_url,puan,sponsor_level").eq("is_active", True).eq("il", il).order("sponsor_level", desc=True).order("puan", desc=True).limit(limit)
    if ilce:
        query = query.eq("ilce", ilce)
    result = query.execute()
    return {"stations": result.data}

@router.get("/stations/summary")
async def stations_summary():
    db = get_supabase()
    all_stations = db.table("stations").select("il,sponsor_level").eq("is_active", True).execute()
    by_il = {}
    for s in all_stations.data:
        il = s["il"]
        if il not in by_il:
            by_il[il] = {"count": 0, "sponsored": 0}
        by_il[il]["count"] += 1
        if s.get("sponsor_level", 0) > 0:
            by_il[il]["sponsored"] += 1
    return {"by_il": by_il, "total": sum(v["count"] for v in by_il.values())}
