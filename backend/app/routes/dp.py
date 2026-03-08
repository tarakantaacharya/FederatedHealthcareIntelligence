"""
Differential privacy routes (Phase 8+)
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def dp_status():
    return {"status": "dp_service_active"}
