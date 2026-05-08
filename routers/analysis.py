from utils.supabase_client import get_supabase
from fastapi import APIRouter
router = APIRouter()

@router.get("/status/{report_id}")
async def get_analysis_status(report_id: str):
    return {"report_id": report_id, "status": "completed"}

from pydantic import BaseModel
from typing import Optional
from agents.orchestrator import analyze_text as run_orchestrator
from datetime import datetime

class ReportAnalysisRequest(BaseModel):
    user_id: Optional[str] = None
    report_text: str
    plaka: Optional[str] = None
    station_name: Optional[str] = None

@router.post("/analysis/report")
async def analyze_report(data: ReportAnalysisRequest):
    db = get_supabase()

    # Analiz hakkı kontrolü
    if data.user_id:
        user = db.table("users").select("free_analyses").eq("id", data.user_id).execute()
        if user.data and user.data[0].get("free_analyses", 0) <= 0:
            from fastapi import HTTPException
            raise HTTPException(status_code=402, detail="Analiz hakkı kalmadı")

    # Raporu DB'ye kaydet
    report_record = {
        "user_id": data.user_id,
        "plaka": data.plaka,
        "station_name": data.station_name,
        "raw_text": data.report_text,
        "status": "processing",
        "created_at": datetime.now().isoformat()
    }
    report_result = db.table("reports").insert(report_record).execute()
    report_id = report_result.data[0]["id"] if report_result.data else None

    try:
        # AI analizi çalıştır
        result = await run_orchestrator(data.report_text, data.user_id or "anonymous")

        # Sonucu kaydet
        if report_id:
            db.table("reports").update({
                "status": "completed",
                "result": result,
                "updated_at": datetime.now().isoformat()
            }).eq("id", report_id).execute()

        # Analiz hakkı düş
        if data.user_id:
            user = db.table("users").select("free_analyses,total_analyses").eq("id", data.user_id).execute()
            if user.data:
                db.table("users").update({
                    "free_analyses": max(0, user.data[0].get("free_analyses", 1) - 1),
                    "total_analyses": user.data[0].get("total_analyses", 0) + 1
                }).eq("id", data.user_id).execute()

        return {"success": True, "report_id": report_id, "result": result}

    except Exception as e:
        if report_id:
            db.table("reports").update({"status": "error"}).eq("id", report_id).execute()
        raise

import tempfile, os
from fastapi import UploadFile, File, Form

@router.post("/analysis/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None)
):
    db = get_supabase()

    # Analiz hakkı kontrolü
    if user_id:
        user = db.table("users").select("free_analyses").eq("id", user_id).execute()
        if user.data and user.data[0].get("free_analyses", 0) <= 0:
            raise HTTPException(status_code=402, detail="Analiz hakkı kalmadı")

    # Dosyayı geçici olarak kaydet
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Raporu DB'ye kaydet
        report_record = {
            "user_id": user_id,
            "status": "processing",
            "created_at": datetime.now().isoformat()
        }
        report_result = db.table("reports").insert(report_record).execute()
        report_id = report_result.data[0]["id"] if report_result.data else None

        # AI analizi — dosya ile
        file_type = "pdf" if suffix.lower() == ".pdf" else "image"
        from agents.orchestrator import analyze_report, analyze_report_smart
        result = await analyze_report_smart(tmp_path, file_type, user_id or "anonymous")

        if report_id:
            db.table("reports").update({
                "status": "completed",
                "result": result,
                "updated_at": datetime.now().isoformat()
            }).eq("id", report_id).execute()

        # Analiz hakkı düş
        if user_id and result.get("success"):
            user = db.table("users").select("free_analyses,total_analyses").eq("id", user_id).execute()
            if user.data:
                db.table("users").update({
                    "free_analyses": max(0, user.data[0].get("free_analyses", 1) - 1),
                    "total_analyses": user.data[0].get("total_analyses", 0) + 1
                }).eq("id", user_id).execute()

        return {"success": True, "report_id": report_id, "result": result}

    finally:
        os.unlink(tmp_path)
