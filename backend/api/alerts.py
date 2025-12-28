"""
Alerts API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import json

router = APIRouter()

ALERTS_LOG_PATH = "backend/data/alerts.json"


class Alert(BaseModel):
    id: str
    timestamp: str
    intrusion_type: str
    detection_count: int
    image_path: Optional[str] = None
    detections: List[dict] = []


@router.get("/", response_model=List[Alert])
async def get_alerts(limit: int = 50, skip: int = 0):
    """Get alert history"""
    try:
        alerts_file = Path(ALERTS_LOG_PATH)
        
        if not alerts_file.exists():
            return []
        
        with open(alerts_file, 'r') as f:
            alerts = json.load(f)
        
        # Sort by timestamp descending
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return alerts[skip:skip + limit]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/latest")
async def get_latest_alert():
    """Get the most recent alert"""
    try:
        alerts_file = Path(ALERTS_LOG_PATH)
        
        if not alerts_file.exists():
            return None
        
        with open(alerts_file, 'r') as f:
            alerts = json.load(f)
        
        if not alerts:
            return None
        
        # Sort and return latest
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        return alerts[0]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest alert: {str(e)}")


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete a specific alert"""
    try:
        alerts_file = Path(ALERTS_LOG_PATH)
        
        if not alerts_file.exists():
            raise HTTPException(status_code=404, detail="Alert not found")
        
        with open(alerts_file, 'r') as f:
            alerts = json.load(f)
        
        # Filter out the alert
        updated_alerts = [a for a in alerts if a['id'] != alert_id]
        
        if len(updated_alerts) == len(alerts):
            raise HTTPException(status_code=404, detail="Alert not found")
        
        with open(alerts_file, 'w') as f:
            json.dump(updated_alerts, f, indent=2)
        
        return {"message": "Alert deleted", "id": alert_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")


@router.delete("/")
async def clear_alerts():
    """Clear all alerts"""
    try:
        alerts_file = Path(ALERTS_LOG_PATH)
        
        if alerts_file.exists():
            with open(alerts_file, 'w') as f:
                json.dump([], f)
        
        return {"message": "All alerts cleared"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear alerts: {str(e)}")