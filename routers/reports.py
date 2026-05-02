from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile, os
from agents.orchestrator import analyze_report

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/png": "image"
}
MAX_SIZE = 10 * 1024 * 1024

@router.post("/upload-and-analyze")
async def upload_and_analyze(file: UploadFile = File(...), user_id: str = "anonymous"):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Sadece PDF, JPG veya PNG dosyası yükleyebilirsiniz.")
    file_type = ALLOWED_TYPES[file.content_type]
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Dosya boyutu 10MB'ı geçemez.")
    suffix = ".pdf" if file_type == "pdf" else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        result = await analyze_report(file_path=tmp_path, file_type=file_type, user_id=user_id)
        if result["success"]:
            return JSONResponse(content=result["data"])
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Analiz başarısız"))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.get("/{report_id}")
async def get_report(report_id: str):
    return {"message": "Faz 2'de aktif edilecek", "report_id": report_id}
