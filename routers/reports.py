from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
from utils.supabase_client import get_supabase

router = APIRouter()

@router.get("/reports")
async def list_reports(limit: int = 50, offset: int = 0, status: Optional[str] = None):
    db = get_supabase()
    query = db.table("reports").select("*").order("created_at", desc=True).range(offset, offset+limit-1)
    if status:
        query = query.eq("status", status)
    result = query.execute()
    return {"reports": result.data, "total": len(result.data)}

@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    db = get_supabase()
    result = db.table("reports").select("*").eq("id", report_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı")
    return result.data[0]

@router.get("/reports/by-plate/{plaka}")
async def get_reports_by_plate(plaka: str):
    db = get_supabase()
    clean = plaka.upper().replace(" ", "")
    result = db.table("reports").select("*").eq("plaka", clean).order("created_at", desc=True).execute()
    return {"reports": result.data, "count": len(result.data)}

@router.put("/reports/{report_id}/status")
async def update_report_status(report_id: str, status: str):
    db = get_supabase()
    db.table("reports").update({"status": status, "updated_at": datetime.now().isoformat()}).eq("id", report_id).execute()
    return {"success": True}
