# src/api/routes/health.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Health check", description="Check if the API is healthy")
async def health_check():
    return {"status": "ok"}