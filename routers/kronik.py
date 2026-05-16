from fastapi import APIRouter
from typing import Optional

router = APIRouter()

@router.get("/kronik")
async def get_kronik(marka: str, model: str, yil: int = 2015, motor_hacmi: Optional[str] = None, beygir: Optional[int] = None):
    from agents.kronik_agent import get_kronik_sorunlar
    sorunlar = await get_kronik_sorunlar(marka, model, yil, motor_hacmi, beygir)
    return {"marka": marka, "model": model, "sorunlar": sorunlar}
