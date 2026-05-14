from fastapi import APIRouter
from typing import Optional
import os, sys
sys.path.append("/opt/ekspertizai")

router = APIRouter()

@router.get("/kronik")
async def get_kronik(marka: str, model: str, yil: int = 2015):
    from agents.kronik_agent import get_kronik_sorunlar
    sorunlar = await get_kronik_sorunlar(marka, model, yil)
    return {"marka": marka, "model": model, "sorunlar": sorunlar}
