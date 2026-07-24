# services/api-gateway/app/api/health.py

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["Health"])

@router.get("/health", summary="健康检查")
async def health_check():
    return {
        "status": "healthy",
        "service": "VPP-API-Gateway",
        "timestamp": datetime.utcnow().isoformat()
    }