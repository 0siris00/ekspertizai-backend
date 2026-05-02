from fastapi import APIRouter, Request
router = APIRouter()

@router.post("/telegram")
async def telegram_incoming(request: Request):
    return {"status": "ok"}

@router.post("/iyzico")
async def iyzico_callback(request: Request):
    return {"status": "ok"}
