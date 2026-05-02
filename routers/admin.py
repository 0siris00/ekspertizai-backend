from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta

router = APIRouter()

class StationCreate(BaseModel):
    ad: str
    franchise: Optional[str] = "Bağımsız"
    il: str
    ilce: str
    adres: Optional[str] = None
    telefon: Optional[str] = None
    telefon2: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    google_maps_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_sponsored: bool = False
    sponsor_level: int = Field(default=0, ge=0, le=2)

class StationUpdate(BaseModel):
    ad: Optional[str] = None
    franchise: Optional[str] = None
    il: Optional[str] = None
    ilce: Optional[str] = None
    adres: Optional[str] = None
    telefon: Optional[str] = None
    is_active: Optional[bool] = None
    is_sponsored: Optional[bool] = None
    sponsor_level: Optional[int] = None

class BulkStationImport(BaseModel):
    franchise: str
    stations: List[StationCreate]

class SkillUpdateRequest(BaseModel):
    report_id: str
    unknown_finding: str
    expert_score: str
    expert_rule: str
    apply_to_skill: str

class ExpertCreate(BaseModel):
    name: str
    phone: str

@router.get("/dashboard")
async def get_dashboard():
    return {"bugun": {"rapor_sayisi": 0, "ilan_analizi": 0, "danismanlik_talebi": 0},
            "toplam": {"rapor": 0, "istasyon": 0, "sponsored_istasyon": 0, "bekleyen_review": 0}}

@router.get("/stations")
async def list_stations(il: Optional[str] = None, ilce: Optional[str] = None,
    franchise: Optional[str] = None, is_sponsored: Optional[bool] = None, page: int = 1):
    return {"stations": [], "total": 0, "page": page}

@router.post("/stations")
async def create_station(data: StationCreate):
    return {"success": True, "message": f"{data.ad} ({data.il}/{data.ilce}) eklendi."}

@router.post("/stations/bulk")
async def bulk_import_stations(data: BulkStationImport):
    return {"success": True, "franchise": data.franchise, "toplam": len(data.stations)}

@router.put("/stations/{station_id}")
async def update_station(station_id: str, data: StationUpdate):
    return {"success": True, "station_id": station_id}

@router.delete("/stations/{station_id}")
async def deactivate_station(station_id: str):
    return {"success": True, "message": "İstasyon pasife alındı."}

@router.post("/stations/{station_id}/sponsor")
async def set_sponsor(station_id: str, level: int = 1, ay: int = 1):
    bitis = datetime.now() + timedelta(days=30 * ay)
    return {"success": True, "station_id": station_id, "sponsor_level": level,
            "bitis": bitis.isoformat(), "ucret": f"{level * 500 * ay:,}₺"}

@router.get("/stations/meta")
async def get_station_meta():
    return {
        "iller": ["Adana","Ankara","Antalya","Balıkesir","Bursa","İstanbul","İzmir",
                  "Kocaeli","Konya","Manisa","Mersin","Samsun","Tekirdağ","Trabzon"],
        "franchiseler": ["Bağımsız","Dynobil","Otorapor","PilotGarage",
                         "Garantili Arabam","Umran Oto Ekspertiz","Dynomoss","Güney Garanti","Diğer"]
    }

@router.get("/review-queue")
async def get_review_queue():
    return {"bekleyen": [], "toplam": 0}

@router.post("/review/{report_id}")
async def submit_review(report_id: str, data: SkillUpdateRequest):
    return {"success": True, "message": f"Kaydedildi → {data.apply_to_skill}_skill.md"}

@router.get("/reports")
async def list_reports(verdict: Optional[str] = None, marka: Optional[str] = None, page: int = 1):
    return {"reports": [], "total": 0, "page": page}

@router.get("/consultations")
async def list_consultations(status: Optional[str] = None):
    return {"consultations": [], "total": 0}

@router.post("/consultations/{consultation_id}/assign")
async def assign_expert(consultation_id: str, expert_id: str):
    return {"success": True}

@router.get("/experts")
async def list_experts():
    return {"experts": []}

@router.post("/experts")
async def add_expert(data: ExpertCreate):
    return {"success": True, "message": f"{data.name} eklendi."}

@router.get("/settings")
async def get_settings():
    return {"settings": {"site_active": True, "max_file_size_mb": 10, "consultation_price": 19900}}

@router.put("/settings/{key}")
async def update_setting(key: str, value: str):
    return {"success": True, "key": key, "value": value}
