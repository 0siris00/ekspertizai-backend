from fastapi import APIRouter
router = APIRouter()

@router.get("/status/{report_id}")
async def get_analysis_status(report_id: str):
    return {"report_id": report_id, "status": "completed"}
