from fastapi import APIRouter
from utils.supabase_client import get_supabase

router = APIRouter()

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    db = get_supabase()
    result = db.table("reports").select("id,status,result").eq("id", job_id).execute()
    if not result.data:
        return {"status": "not_found"}
    row = result.data[0]
    if row["status"] == "completed" and row["result"]:
        return {"status": "completed", "result": row["result"]}
    elif row["status"] == "error":
        return {"status": "error", "message": "Analiz başarısız oldu."}
    else:
        return {"status": "processing"}
