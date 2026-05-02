from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter()

class ConsultationRequest(BaseModel):
    report_id: str
    preferred_time: str
    user_phone: str

@router.post("/request")
async def request_consultation(data: ConsultationRequest):
    return {"success": True, "message": "Talep alındı. Ödeme sayfasına yönlendiriliyorsunuz."}

@router.patch("/{consultation_id}/complete")
async def complete_consultation(consultation_id: str, notes: str = ""):
    return {"success": True}
