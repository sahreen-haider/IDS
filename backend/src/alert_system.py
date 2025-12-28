"""
Alert system for intrusion detection events
"""
import cv2
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import numpy as np
import json
import uuid


logger = logging.getLogger(__name__)


class AlertSystem:
    """Handle alerts when intrusions are detected"""
    
    def __init__(
        self,
        save_path: str = "data/detections",
        alert_cooldown: int = 30,
        enable_sound: bool = True,
        enable_save: bool = True
    ):
        """
        Initialize alert system
        
        Args:
            save_path: Directory to save detection images
            alert_cooldown: Cooldown period between alerts (seconds)
            enable_sound: Enable sound alerts
            enable_save: Enable saving detection images
        """
        self.save_path = Path(save_path)
        self.alert_cooldown = alert_cooldown
        self.enable_sound = enable_sound
        self.enable_save = enable_save
        
        # Create save directory
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        # Alert log file
        self.alert_log_path = Path("backend/data/alerts.json")
        self.alert_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize alert log if it doesn't exist
        if not self.alert_log_path.exists():
            with open(self.alert_log_path, 'w') as f:
                json.dump([], f)
        
        # Track last alert time
        self.last_alert_time = 0
        
        # Statistics
        self.total_alerts = 0
        self.alerts_by_type = {}
    
    def trigger_alert(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        intrusion_type: str
    ) -> bool:
        """
        Trigger alert for detected intrusion
        
        Args:
            frame: Image frame with detection
            detections: List of detections
            intrusion_type: Type of intrusion ('human', 'animal', 'object')
            
        Returns:
            True if alert triggered, False if in cooldown
        """
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_alert_time < self.alert_cooldown:
            return False
        
        # Update last alert time
        self.last_alert_time = current_time
        
        # Update statistics
        self.total_alerts += 1
        self.alerts_by_type[intrusion_type] = self.alerts_by_type.get(intrusion_type, 0) + 1
        
        # Log alert
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.warning(f"⚠️  INTRUSION DETECTED - Type: {intrusion_type} - Time: {timestamp}")
        logger.info(f"   Detected objects: {[d['class_name'] for d in detections]}")
        
        # Save image and get filename
        image_path = None
        if self.enable_save:
            image_path = self._save_detection(frame, detections, intrusion_type)
        
        # Log to JSON file
        self._log_alert_to_json(intrusion_type, detections, timestamp, image_path)
        
        # Sound alert
        if self.enable_sound:
            self._play_alert_sound()
        
        return True
    
    def _save_detection(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        intrusion_type: str
    ) -> str:
        """Save detection image to disk and return relative path"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{intrusion_type}_{timestamp}.jpg"
            filepath = self.save_path / filename
            
            cv2.imwrite(str(filepath), frame)
            logger.info(f"Detection saved: {filepath}")
            
            # Return relative path from backend directory
            return f"data/detections/{filename}"
            
        except Exception as e:
            logger.error(f"Failed to save detection image: {e}")
    
    def _play_alert_sound(self):
        """Play alert sound (system beep)"""
        try:
            # Windows beep
            if os.name == 'nt':
                import winsound
                winsound.Beep(1000, 500)  # 1000 Hz for 500ms
            else:
                # Unix beep
                print('\a')
        except Exception as e:
            logger.debug(f"Sound alert failed: {e}")
    
    def _log_alert_to_json(
        self,
        intrusion_type: str,
        detections: List[Dict],
        timestamp: str,
        image_path: str = None
    ):
        """Log alert to JSON file for API consumption"""
        try:
            # Read existing alerts
            with open(self.alert_log_path, 'r') as f:
                alerts = json.load(f)
            
            # Create alert entry
            alert = {
                'id': str(uuid.uuid4()),
                'timestamp': timestamp,
                'intrusion_type': intrusion_type,
                'detection_count': len(detections),
                'image_path': image_path,
                'detections': [
                    {
                        'class_name': d['class_name'],
                        'confidence': float(d['confidence'])
                    }
                    for d in detections
                ]
            }
            
            # Add to beginning of list (most recent first)
            alerts.insert(0, alert)
            
            # Keep only last 100 alerts
            alerts = alerts[:100]
            
            # Save back to file
            with open(self.alert_log_path, 'w') as f:
                json.dump(alerts, f, indent=2)
            
            logger.debug(f"Alert logged to {self.alert_log_path}")
            
        except Exception as e:
            logger.error(f"Failed to log alert to JSON: {e}")
    
    def get_statistics(self) -> Dict:
        """
        Get alert statistics
        
        Returns:
            Dictionary with alert statistics
        """
        return {
            'total_alerts': self.total_alerts,
            'alerts_by_type': self.alerts_by_type,
            'last_alert': datetime.fromtimestamp(self.last_alert_time).strftime("%Y-%m-%d %H:%M:%S")
            if self.last_alert_time > 0 else "None"
        }
    
    def reset_statistics(self):
        """Reset alert statistics"""
        self.total_alerts = 0
        self.alerts_by_type = {}
        logger.info("Alert statistics reset")
