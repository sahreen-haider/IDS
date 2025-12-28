"""
FastAPI Backend for Intrusion Detection System
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
from pathlib import Path
import uvicorn

from .api import alerts, config, stats, live
from .src.detection_service import DetectionService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IDS API",
    description="Intrusion Detection System API",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for saved detections
detections_path = Path("backend/data/detections")
detections_path.mkdir(parents=True, exist_ok=True)
app.mount("/detections", StaticFiles(directory=str(detections_path)), name="detections")

# Mount frontend files
try:
    frontend_path = Path("frontend")
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
        logger.info("Frontend mounted at /")
except Exception as e:
    logger.warning(f"Could not mount frontend: {e}")

# Include routers
app.include_router(config.router, prefix="/api/config", tags=["Configuration"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(live.router, prefix="/api/live", tags=["Live Feed"])

# Global detection service instance
detection_service: DetectionService = None


@app.on_event("startup")
async def startup_event():
    """Initialize detection service on startup"""
    global detection_service
    logger.info("Starting Intrusion Detection System API...")
    
    try:
        detection_service = DetectionService(config_path="shared/config.yaml")
        detection_service.start()
        logger.info("Detection service started successfully")
    except Exception as e:
        logger.error(f"Failed to start detection service: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global detection_service
    logger.info("Shutting down Intrusion Detection System API...")
    
    if detection_service:
        detection_service.stop()
        logger.info("Detection service stopped")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Intrusion Detection System API",
        "version": "1.0.0",
        "status": "running" if detection_service and detection_service.is_running else "stopped"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "detection_running": detection_service.is_running if detection_service else False,
        "camera_connected": detection_service.camera_connected if detection_service else False
    }


@app.post("/api/detection/start")
async def start_detection():
    """Start detection service"""
    global detection_service
    
    if not detection_service:
        detection_service = DetectionService(config_path="shared/config.yaml")
    
    if detection_service.is_running:
        return {"message": "Detection already running", "status": "running"}
    
    try:
        detection_service.start()
        return {"message": "Detection started", "status": "running"}
    except Exception as e:
        logger.error(f"Failed to start detection: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Failed to start detection: {str(e)}"}
        )


@app.post("/api/detection/stop")
async def stop_detection():
    """Stop detection service"""
    global detection_service
    
    if not detection_service or not detection_service.is_running:
        return {"message": "Detection not running", "status": "stopped"}
    
    try:
        detection_service.stop()
        return {"message": "Detection stopped", "status": "stopped"}
    except Exception as e:
        logger.error(f"Failed to stop detection: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Failed to stop detection: {str(e)}"}
        )


def get_detection_service():
    """Dependency to get detection service"""
    return detection_service


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
