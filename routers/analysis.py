from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form

import asyncio

async def do_analysis_background(report_id: str, tmp_path: str, file_type: str, user_id: str):
    from utils.supabase_client import get_supabase
    from agents.orchestrator import analyze_report_smart
    from datetime import datetime
    import os
    db = get_supabase()
    try:
        result = await analyze_report_smart(tmp_path, file_type, user_id or "anonymous")
        db.table("reports").update({
            "status": "completed",
            "result": result,
            "updated_at": datetime.now().isoformat()
        }).eq("id", report_id).execute()
        if user_id and result.get("success"):
            user = db.table("users").select("free_analyses,total_analyses").eq("id", user_id).execute()
            if user.data:
                db.table("users").update({
                    "free_analyses": max(0, user.data[0].get("free_analyses", 1) - 1),
                    "total_analyses": user.data[0].get("total_analyses", 0) + 1
                }).eq("id", user_id).execute()
    except Exception as e:
        db.table("reports").update({"status": "error", "updated_at": datetime.now().isoformat()}).eq("id", report_id).execute()
    finally:
        try: os.unlink(tmp_path)
        except: pass

from utils.supabase_client import get_supabase
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

@router.post("/analysis/upload")
async def upload_and_analyze(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    file1: Optional[UploadFile] = File(None),
    file2: Optional[UploadFile] = File(None),
    file3: Optional[UploadFile] = File(None),
    user_id: Optional[str] = Form(None)
):
    db = get_supabase()

    # Analiz hakkı kontrolü
    if user_id:
        user = db.table("users").select("free_analyses").eq("id", user_id).execute()
        if user.data and user.data[0].get("free_analyses", 0) <= 0:
            raise HTTPException(status_code=402, detail="Analiz hakkı kalmadı")

    # Tüm dosyaları birleştir
    all_files = [file] + [f for f in [file1, file2, file3] if f is not None]
    
    # İlk dosyayı ana dosya olarak kullan, diğerlerini metin olarak ekle
    suffix = os.path.splitext(all_files[0].filename)[1] if all_files[0].filename else ".pdf"
    content = await all_files[0].read()
    
    # Diğer dosyaların metinlerini birleştir
    extra_texts = []
    for extra_file in all_files[1:]:
        try:
            extra_content = await extra_file.read()
            extra_suffix = os.path.splitext(extra_file.filename)[1] if extra_file.filename else ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=extra_suffix) as etmp:
                etmp.write(extra_content)
                etmp_path = etmp.name
            from agents.agent1_reader import extract_text_from_pdf, extract_text_from_image
            if extra_suffix.lower() == '.pdf':
                extra_texts.append(extract_text_from_pdf(etmp_path))
            else:
                extra_texts.append(extract_text_from_image(etmp_path))
            os.unlink(etmp_path)
        except:
            pass
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    # Dosya hash hesapla — aynı dosya tekrar yüklenirse eski analizi dön
    import hashlib
    content_hash = hashlib.md5(content).hexdigest()

    existing = db.table("reports").select("id,status,result").eq("file_hash", content_hash).eq("status", "completed").execute()
    if existing.data and existing.data[0].get("result"):
        os.unlink(tmp_path)
        old_report = existing.data[0]
        # Bu kullanıcıya da kaydet
        if user_id:
            db.table("reports").insert({
                "user_id": user_id,
                "file_hash": content_hash,
                "status": "completed",
                "result": old_report["result"],
                "created_at": datetime.now().isoformat()
            }).execute()
        return {"success": True, "report_id": old_report["id"], "status": "completed", "cached": True}

    # Raporu DB'ye kaydet
    report_record = {
        "user_id": user_id,
        "file_hash": content_hash,
        "status": "processing",
        "created_at": datetime.now().isoformat()
    }
    report_result = db.table("reports").insert(report_record).execute()
    report_id = report_result.data[0]["id"] if report_result.data else None

    file_type = "pdf" if suffix.lower() == ".pdf" else "image"

    # Arka planda analiz başlat
    background_tasks.add_task(do_analysis_background, report_id, tmp_path, file_type, user_id or "anonymous")

    return {"success": True, "report_id": report_id, "status": "processing"}
