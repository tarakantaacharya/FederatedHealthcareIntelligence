"""
Monitoring Routes (Phase 37)
Prometheus metrics and health endpoints
"""
from fastapi import APIRouter, Response
from app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format
    """
    metrics = MonitoringService.get_metrics()
    return Response(content=metrics, media_type="text/plain")


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns detailed health status
    """
    return MonitoringService.health_check()


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe
    
    Returns 200 if service is ready to accept traffic
    """
    health = MonitoringService.health_check()
    
    if health['status'] in ['healthy', 'degraded']:
        return {"status": "ready"}
    else:
        return Response(status_code=503, content="Not ready")


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe
    
    Returns 200 if service is alive
    """
    return {"status": "alive"}
