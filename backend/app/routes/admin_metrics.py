"""
Admin metrics routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.utils.auth import require_role
from app.services.admin_metrics_service import AdminMetricsService

router = APIRouter()


@router.get("/metrics")
async def get_admin_metrics(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role("ADMIN"))
):
    """Return dynamic admin dashboard metrics."""
    return AdminMetricsService.get_admin_metrics(db)
