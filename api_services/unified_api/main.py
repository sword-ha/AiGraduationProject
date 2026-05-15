import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from id_verification.routers.id_router import router as id_router
from personality.routers.personality_router import router as personality_router
from cv_generator_svc.routers.cv_router import router as cv_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="AI Graduation Project — Unified API",
    description=(
        "Single endpoint for all AI microservices.\n\n"
        "| Prefix | Service |\n"
        "|--------|--------|\n"
        "| `/api/v1/id/...` | Egyptian ID Verification |\n"
        "| `/api/v1/personality/...` | MBTI Personality Analysis |\n"
        "| `/api/v1/cv/...` | CV Generator |\n"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(id_router, prefix="/api/v1/id")
app.include_router(personality_router, prefix="/api/v1/personality")
app.include_router(cv_router, prefix="/api/v1/cv")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "unified-api"}


@app.get("/services", tags=["Health"])
async def services():
    return {
        "id_verification": "POST /api/v1/id/verify-id",
        "personality": "GET /api/v1/personality/questions  |  POST /api/v1/personality/analyze-personality",
        "cv_generator": "POST /api/v1/cv/generate-cv  |  GET /api/v1/cv/download-cv/{filename}",
    }
