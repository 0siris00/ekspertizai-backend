from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="EkspertizAI API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import reports, analysis, consultation, admin, stations, webhook

app.include_router(reports.router, prefix="/api/reports", tags=["Raporlar"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analiz"])
app.include_router(consultation.router, prefix="/api/consultation", tags=["Danışmanlık"])
app.include_router(admin.router, prefix="/api/admin", tags=["Yönetim"])
app.include_router(stations.router, prefix="/api/stations", tags=["İstasyonlar"])
app.include_router(webhook.router, prefix="/api/webhook", tags=["Webhook"])

@app.get("/")
def root():
    return {"status": "ok", "service": "EkspertizAI", "version": "2.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup():
    from utils.telegram import notify_admin
    await notify_admin("🚀 EkspertizAI sunucusu başlatıldı!")
    print("🚀 EkspertizAI başlatıldı")
