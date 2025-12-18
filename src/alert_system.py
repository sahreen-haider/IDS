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
        
        # Save image
        if self.enable_save:
            self._save_detection(frame, detections, intrusion_type)
        
        # Sound alert
        if self.enable_sound:
            self._play_alert_sound()
        
        return True
    
    def _save_detection(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        intrusion_type: str
    ):
        """Save detection image to disk"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{intrusion_type}_{timestamp}.jpg"
            filepath = self.save_path / filename
            
            cv2.imwrite(str(filepath), frame)
            logger.info(f"Detection saved: {filepath}")
            
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
