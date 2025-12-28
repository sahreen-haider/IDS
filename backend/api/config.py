"""
Configuration API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import yaml
from pathlib import Path

router = APIRouter()

CONFIG_PATH = "shared/config.yaml"


class CameraConfig(BaseModel):
    url: str | int
    width: int
    height: int
    fps: int


class ModelConfig(BaseModel):
    weights: str
    confidence_threshold: float
    iou_threshold: float
    device: str


class DetectionConfig(BaseModel):
    target_classes: List[str]
    perimeter_zone: List[List[float]]
    enable_perimeter: bool
    alert_cooldown: int
    min_detection_size: float
    frame_skip: int
    use_half_precision: bool
    inference_size: int


class AlertConfig(BaseModel):
    sound: bool
    save_image: bool
    save_video: bool
    console_log: bool
    save_path: str


class ConfigResponse(BaseModel):
    camera: CameraConfig
    model: ModelConfig
    detection: DetectionConfig
    alerts: AlertConfig


@router.get("/", response_model=ConfigResponse)
async def get_config():
    """Get current configuration"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        return {
            "camera": config.get('camera', {}),
            "model": config.get('model', {}),
            "detection": config.get('detection', {}),
            "alerts": config.get('alerts', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load config: {str(e)}")


@router.put("/camera")
async def update_camera_config(camera: CameraConfig):
    """Update camera configuration"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        config['camera'] = camera.dict()
        
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return {"message": "Camera config updated", "camera": camera}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.put("/detection")
async def update_detection_config(detection: DetectionConfig):
    """Update detection configuration"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        config['detection'] = detection.dict()
        
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return {"message": "Detection config updated", "detection": detection}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.put("/perimeter")
async def update_perimeter(perimeter_zone: List[List[float]], enable: bool = True):
    """Update perimeter zone"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        config['detection']['perimeter_zone'] = perimeter_zone
        config['detection']['enable_perimeter'] = enable
        
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return {
            "message": "Perimeter updated",
            "perimeter_zone": perimeter_zone,
            "enabled": enable
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update perimeter: {str(e)}")
