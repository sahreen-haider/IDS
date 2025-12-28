"""
Statistics API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

router = APIRouter()


class SystemStats(BaseModel):
    fps: float
    detection_fps: float
    detection_count: int
    in_perimeter: int
    outside_perimeter: int


class AlertStats(BaseModel):
    total_alerts: int
    alerts_by_type: Dict[str, int]
    last_alert: str


@router.get("/system", response_model=SystemStats)
async def get_system_stats():
    """Get real-time system statistics"""
    from ..main import detection_service
    
    if not detection_service or not detection_service.is_running:
        return {
            "fps": 0,
            "detection_fps": 0,
            "detection_count": 0,
            "in_perimeter": 0,
            "outside_perimeter": 0
        }
    
    try:
        stats = detection_service.get_latest_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/alerts", response_model=AlertStats)
async def get_alert_stats():
    """Get alert statistics"""
    from ..main import detection_service
    
    if not detection_service:
        return {
            "total_alerts": 0,
            "alerts_by_type": {},
            "last_alert": "None"
        }
    
    try:
        stats = detection_service.get_alert_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert stats: {str(e)}")


@router.get("/detections")
async def get_current_detections():
    """Get current frame detections"""
    from ..main import detection_service
    
    if not detection_service or not detection_service.is_running:
        return {"detections": [], "count": 0}
    
    try:
        detections = detection_service.get_latest_detections()
        return {
            "detections": detections,
            "count": len(detections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get detections: {str(e)}")