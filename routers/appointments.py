from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from utils.supabase_client import get_supabase
from utils.telegram import notify_admin

router = APIRouter()

class AppointmentRequest(BaseModel):
    user_id: Optional[str] = None
    user_phone: str
    user_name: Optional[str] = None
    station_name: str
    station_id: Optional[str] = None
    preferred_date: str
    preferred_time: str
    vehicle_info: Optional[str] = None
    report_id: Optional[str] = None

class AppointmentAction(BaseModel):
    status: str
    admin_note: Optional[str] = None

@router.post("/appointments/request")
async def request_appointment(data: AppointmentRequest):
    db = get_supabase()
    record = {
        "user_id": data.user_id,
        "user_phone": data.user_phone,
        "user_name": data.user_name,
        "station_name": data.station_name,
        "station_id": data.station_id,
        "preferred_date": data.preferred_date,
        "preferred_time": data.preferred_time,
        "vehicle_info": data.vehicle_info,
        "report_id": data.report_id,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    result = db.table("appointments").insert(record).execute()
    appointment_id = result.data[0]["id"] if result.data else "?"
    msg = (
        f"📅 YENİ RANDEVU TALEBİ\n\n"
        f"👤 {data.user_name or 'Bilinmiyor'} · {data.user_phone}\n"
        f"🏢 {data.station_name}\n"
        f"📆 {data.preferred_date} · {data.preferred_time}\n"
        f"🚗 {data.vehicle_info or '-'}\n"
        f"ID: {appointment_id}"
    )
    await notify_admin(msg)
    return {"success": True, "appointment_id": appointment_id, "message": "Randevu talebiniz alındı."}

@router.get("/appointments")
async def list_appointments(status: Optional[str] = None):
    db = get_supabase()
    query = db.table("appointments").select("*").order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    result = query.execute()
    return {"appointments": result.data}

@router.put("/appointments/{appointment_id}")
async def update_appointment(appointment_id: str, data: AppointmentAction):
    if data.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Geçersiz durum")
    db = get_supabase()
    db.table("appointments").update({
        "status": data.status,
        "admin_note": data.admin_note,
        "updated_at": datetime.now().isoformat()
    }).eq("id", appointment_id).execute()
    return {"success": True, "status": data.status}
