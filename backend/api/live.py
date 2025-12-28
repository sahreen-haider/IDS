"""
Live video streaming via WebSocket
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import cv2
import asyncio
import logging
import numpy as np

router = APIRouter()
logger = logging.getLogger(__name__)


async def generate_frames():
    """Generate video frames for streaming"""
    from ..main import detection_service
    
    if not detection_service or not detection_service.is_running:
        # Return a blank frame if service not running
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank, "Detection Service Not Running", (100, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        ret, buffer = cv2.imencode('.jpg', blank)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        return
    
    while True:
        try:
            frame = detection_service.get_latest_frame()
            
            if frame is None:
                await asyncio.sleep(0.033)  # ~30 FPS
                continue
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            
            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            await asyncio.sleep(0.033)  # ~30 FPS
        
        except Exception as e:
            logger.error(f"Error generating frame: {e}")
            await asyncio.sleep(0.1)


@router.get("/stream")
async def video_stream():
    """
    HTTP streaming endpoint for live video feed
    Returns MJPEG stream
    """
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live video and stats
    Sends JSON with base64 encoded frame and statistics
    """
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        from ..main import detection_service
        
        while True:
            if detection_service and detection_service.is_running:
                # Get frame
                frame = detection_service.get_latest_frame()
                stats = detection_service.get_latest_stats()
                detections = detection_service.get_latest_detections()
                
                if frame is not None:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ret:
                        import base64
                        frame_b64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # Send data as JSON
                        await websocket.send_json({
                            "frame": frame_b64,
                            "stats": stats,
                            "detections": detections,
                            "timestamp": asyncio.get_event_loop().time()
                        })
            else:
                # Send status message
                await websocket.send_json({
                    "status": "not_running",
                    "message": "Detection service is not running"
                })
            
            await asyncio.sleep(0.1)  # 10 FPS for WebSocket
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed")