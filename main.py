from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from routers.reports import router as reports_router
from routers.analysis import router as analysis_router
from routers.consultation import router as consultation_router
from routers.admin import router as admin_router
from routers.stations import router as stations_router
from routers.webhook import router as webhook_router
from routers.reviews import router as reviews_router
from routers.referrals import router as referrals_router
from routers.users import router as users_router
from routers.archive import router as archive_router
from routers.appointments import router as appointments_router
from routers.jobs import router as jobs_router
from routers.kronik import router as kronik_router
from routers.jobs import router as jobs_router
from routers.kronik import router as kronik_router
from utils.telegram import notify_admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    await notify_admin("🚀 EkspertizAI başlatıldı")
    yield

app = FastAPI(title="EkspertizAI API", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ekspertizai.com", "https://www.ekspertizai.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports_router, prefix="/api/v1", tags=["reports"])
app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])
app.include_router(consultation_router, prefix="/api/v1", tags=["consultation"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(stations_router, prefix="/api/v1", tags=["stations"])
app.include_router(webhook_router, prefix="/api/v1", tags=["webhook"])
app.include_router(reviews_router, prefix="/api/v1", tags=["reviews"])
app.include_router(referrals_router, prefix="/api/v1", tags=["referrals"])
app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(archive_router, prefix="/api/v1", tags=["archive"])
app.include_router(kronik_router, prefix="/api/v1", tags=["kronik"])
app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])
app.include_router(kronik_router, prefix="/api/v1", tags=["kronik"])
app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])
app.include_router(appointments_router, prefix="/api/v1", tags=["appointments"])

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return JSONResponse({"message": "EkspertizAI API"})
