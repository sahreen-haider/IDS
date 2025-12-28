"""
Camera handler for Android phone and other camera sources
"""
import cv2
import numpy as np
import requests
from typing import Optional, Tuple
import logging
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Tuple
import logging


logger = logging.getLogger(__name__)


class CameraHandler:
    """Handle camera input from Android phone or other sources"""
    
    def __init__(self, camera_url: str, width: int = 1280, height: int = 720):
        """
        Initialize camera handler
        
        Args:
            camera_url: Camera URL (IP webcam URL or device index)
            width: Desired frame width
            height: Desired frame height
        """
        self.camera_url = camera_url
        self.width = width
        self.height = height
        self.capture = None
        self.is_connected = False
        self.snapshot_mode = False
        self.session = None
        
    def connect(self) -> bool:
        """
        Connect to camera source
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Handle both URL strings and device indices
            if isinstance(self.camera_url, str) and self.camera_url.startswith('http'):
                logger.info(f"Connecting to Android camera at {self.camera_url}")
                # Try stream first (MJPEG)
                self.capture = cv2.VideoCapture(self.camera_url)
            else:
                # Local camera (webcam)
                device_id = int(self.camera_url) if isinstance(self.camera_url, str) else self.camera_url
                logger.info(f"Connecting to local camera device {device_id}")
                self.capture = cv2.VideoCapture(device_id)
            
            # Set resolution when using VideoCapture
            if self.capture is not None:
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # Test connection
            if isinstance(self.camera_url, str) and self.camera_url.startswith('http'):
                if self.capture is not None and self.capture.isOpened():
                    ret, _ = self.capture.read()
                    if not ret:
                        logger.warning("Stream opened but failed to read frame; will attempt snapshot mode")
                        self.capture.release()
                        self.capture = None
                    else:
                        self.is_connected = True
                        logger.info("Camera connected successfully")
                        return True
                
                # Fallback to snapshot mode for endpoints like /shot.jpg
                parsed = urlparse(self.camera_url)
                if parsed.path.endswith('shot.jpg') or 'snapshot' in parsed.query:
                    logger.info("Using snapshot mode for camera")
                    self.session = requests.Session()
                    retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
                    self.session.mount('http://', HTTPAdapter(max_retries=retries))
                    self.session.mount('https://', HTTPAdapter(max_retries=retries))
                    # Test one snapshot
                    resp = self.session.get(self.camera_url, timeout=5)
                    if resp.status_code == 200 and resp.content:
                        self.snapshot_mode = True
                        self.is_connected = True
                        logger.info("Camera connected successfully (snapshot mode)")
                        return True
                    else:
                        logger.error("Failed to fetch snapshot from camera")
                        return False
                else:
                    logger.error("Failed to open camera stream; ensure MJPEG endpoint like /video or use /shot.jpg")
                    return False
            else:
                if self.capture is None or not self.capture.isOpened():
                    logger.error("Failed to open camera")
                    return False
                ret, _ = self.capture.read()
                if not ret:
                    logger.error("Failed to read frame from camera")
                    return False
            
            self.is_connected = True
            logger.info("Camera connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to camera: {e}")
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read frame from camera
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_connected or self.capture is None:
            return False, None
        
        try:
            if self.snapshot_mode:
                resp = self.session.get(self.camera_url, timeout=5)
                if resp.status_code != 200:
                    logger.warning(f"Snapshot request failed with status {resp.status_code}")
                    return False, None
                data = np.frombuffer(resp.content, dtype=np.uint8)
                frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
                if frame is None:
                    logger.warning("Failed to decode snapshot frame")
                    return False, None
                return True, frame
            
            ret, frame = self.capture.read()
            if not ret:
                logger.warning("Failed to read frame")
                return False, None
            return True, frame
            
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return False, None
    
    def release(self):
        """Release camera resources"""
        if self.capture is not None:
            self.capture.release()
        if self.session is not None:
            self.session.close()
        self.is_connected = False
        self.snapshot_mode = False
        logger.info("Camera released")
    
    def get_fps(self) -> float:
        """Get camera FPS"""
        if self.capture is not None:
            return self.capture.get(cv2.CAP_PROP_FPS)
        return 0.0
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get actual camera resolution"""
        if self.capture is not None:
            width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return width, height
        return 0, 0
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
