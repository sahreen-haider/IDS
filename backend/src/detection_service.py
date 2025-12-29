"""
Background detection service for continuous monitoring
"""
import threading
import time
import cv2
import logging
import numpy as np
from queue import Queue
from typing import Optional, Dict, List
from pathlib import Path

from .config import Config
from .camera import CameraHandler
from .detector import IntrusionDetector
from .alert_system import AlertSystem

logger = logging.getLogger(__name__)


class DetectionService:
    """Background service for continuous intrusion detection"""
    
    def __init__(self, config_path: str = "shared/config.yaml"):
        """
        Initialize detection service
        
        Args:
            config_path: Path to configuration file
        """
        self.config = Config(config_path)
        self.is_running = False
        self.camera_connected = False
        self.detection_thread: Optional[threading.Thread] = None
        
        # Frame queue for live streaming
        self.frame_queue = Queue(maxsize=10)
        self.latest_frame = None
        self.latest_detections = []
        self.latest_stats = {
            'fps': 0,
            'detection_count': 0,
            'in_perimeter': 0,
            'outside_perimeter': 0
        }
        
        # Components
        self.camera: Optional[CameraHandler] = None
        self.detector: Optional[IntrusionDetector] = None
        self.alert_system: Optional[AlertSystem] = None
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def initialize_components(self):
        """Initialize camera, detector, and alert system"""
        try:
            # Initialize camera
            self.camera = CameraHandler(
                camera_url=self.config.camera_url,
                width=self.config.camera_width,
                height=self.config.camera_height
            )
            
            if not self.camera.connect():
                raise Exception("Failed to connect to camera")
            
            self.camera_connected = True
            logger.info("Camera connected")
            
            # Initialize detector
            self.detector = IntrusionDetector(
                model_path=self.config.model_weights,
                target_classes=self.config.target_classes,
                confidence_threshold=self.config.confidence_threshold,
                device=self.config.get('model.device', 'cpu'),
                inference_size=self.config.inference_size,
                use_half=self.config.use_half_precision,
                perimeter_zone=self.config.perimeter_zone
            )
            
            if not self.detector.load_model():
                raise Exception("Failed to load YOLO model")
            
            # Set perimeter
            frame_width, frame_height = self.camera.get_resolution()
            self.detector.set_perimeter_pixels(frame_width, frame_height)
            logger.info("Detector initialized")
            
            # Initialize alert system
            self.alert_system = AlertSystem(
                save_path=self.config.get('alerts.save_path', 'backend/data/detections'),
                alert_cooldown=self.config.alert_cooldown,
                enable_sound=self.config.get('alerts.sound', True),
                enable_save=self.config.get('alerts.save_image', True)
            )
            logger.info("Alert system initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            self.cleanup()
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        if self.camera:
            self.camera.release()
            self.camera_connected = False
        
        cv2.destroyAllWindows()
    
    def detection_loop(self):
        """Main detection loop running in background thread"""
        frame_count = 0
        detection_frame_count = 0
        fps_start_time = time.time()
        fps = 0
        frame_skip = self.config.frame_skip
        last_detections = []
        last_all_detections = []
        
        logger.info("Detection loop started")
        
        try:
            while self.is_running:
                # Read frame
                ret, frame = self.camera.read_frame()
                if not ret:
                    logger.warning("Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                # Recalculate perimeter pixels if needed (e.g., after perimeter zone update)
                if self.detector.perimeter_pixels is None and self.detector.perimeter_zone:
                    frame_height, frame_width = frame.shape[:2]
                    self.detector.set_perimeter_pixels(frame_width, frame_height)
                    logger.info("Perimeter zone recalculated")
                
                # Perform detection with frame skipping
                if frame_count % frame_skip == 0:
                    all_detections = self.detector.detect(frame)
                    
                    # Filter by perimeter
                    if self.config.enable_perimeter:
                        detections = self.detector.filter_detections_by_perimeter(all_detections)
                    else:
                        detections = all_detections
                    
                    last_detections = detections
                    last_all_detections = all_detections
                    detection_frame_count += 1
                else:
                    detections = last_detections
                    all_detections = last_all_detections
                
                # Check for intrusions
                if detections:
                    intrusion_type = self.detector.classify_intrusion_type(detections)
                    alert_triggered = self.alert_system.trigger_alert(
                        frame, detections, intrusion_type
                    )
                    
                    if alert_triggered:
                        logger.warning(f"ALERT: {intrusion_type.upper()} entered perimeter!")
                
                # Draw perimeter and detections
                display_frame = frame.copy()
                
                if self.config.enable_perimeter:
                    display_frame = self.detector.draw_perimeter_zone(display_frame)
                
                if self.config.get('display.draw_boxes', True):
                    display_frame = self.detector.draw_detections(
                        display_frame,
                        detections,
                        draw_confidence=True
                    )
                
                # Calculate FPS
                frame_count += 1
                if frame_count >= 30:
                    fps = frame_count / (time.time() - fps_start_time)
                    frame_count = 0
                    fps_start_time = time.time()
                
                # Update stats
                with self.lock:
                    self.latest_frame = display_frame
                    self.latest_detections = detections
                    self.latest_stats = {
                        'fps': round(fps, 1),
                        'detection_fps': round(fps / frame_skip if frame_skip > 0 else fps, 1),
                        'detection_count': len(all_detections),
                        'in_perimeter': len(detections),
                        'outside_perimeter': len(all_detections) - len(detections)
                    }
                
                # Update frame queue for streaming
                if not self.frame_queue.full():
                    self.frame_queue.put(display_frame)
                
                # Display window if enabled
                if self.config.show_window:
                    cv2.imshow("IDS - Intrusion Detection System", display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop()
                        break
        
        except Exception as e:
            logger.error(f"Error in detection loop: {e}", exc_info=True)
        
        finally:
            logger.info("Detection loop stopped")
    
    def start(self):
        """Start the detection service"""
        if self.is_running:
            logger.warning("Detection service already running")
            return
        
        logger.info("Starting detection service...")
        
        if not self.initialize_components():
            raise Exception("Failed to initialize detection components")
        
        self.is_running = True
        self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.detection_thread.start()
        logger.info("Detection service running")
        
        logger.info("Detection service started")
    
    def stop(self):
        """Stop the detection service"""
        if not self.is_running:
            logger.warning("Detection service not running")
            return
        
        logger.info("Stopping detection service...")
        self.is_running = False
        
        # Wait for detection thread to finish
        if self.detection_thread and self.detection_thread.is_alive():
            logger.info("Waiting for detection thread to stop...")
            self.detection_thread.join(timeout=3)
            if self.detection_thread.is_alive():
                logger.warning("Detection thread did not stop gracefully")
        
        # Cleanup resources
        self.cleanup()
        logger.info("Detection service stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Close OpenCV windows
            cv2.destroyAllWindows()
            
            # Release camera
            if self.camera:
                self.camera.disconnect()
                logger.info("Camera disconnected")
            
            # Clear queues
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except:
                    break
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the latest processed frame"""
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def get_latest_detections(self) -> List[Dict]:
        """Get the latest detections"""
        with self.lock:
            return self.latest_detections.copy()
    
    def get_latest_stats(self) -> Dict:
        """Get the latest statistics"""
        with self.lock:
            return self.latest_stats.copy()
    
    def get_alert_statistics(self) -> Dict:
        """Get alert system statistics"""
        if self.alert_system:
            return self.alert_system.get_statistics()
        return {}
