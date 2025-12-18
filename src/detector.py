"""
YOLO-based object detector for intrusion detection
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import logging


logger = logging.getLogger(__name__)


class IntrusionDetector:
    """YOLO-based detector for identifying intruders"""
    
    def __init__(
        self,
        model_path: str,
        target_classes: List[str],
        confidence_threshold: float = 0.5,
        device: str = 'cpu'
    ):
        """
        Initialize intrusion detector
        
        Args:
            model_path: Path to YOLO model weights
            target_classes: List of class names to detect
            confidence_threshold: Minimum confidence for detection
            device: Device to run inference on ('cpu', 'cuda', 'mps')
        """
        self.model_path = model_path
        self.target_classes = target_classes
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = None
        
    def load_model(self) -> bool:
        """
        Load YOLO model
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading YOLO model from {self.model_path}")
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            logger.info(f"Model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in frame
        
        Args:
            frame: Input image frame
            
        Returns:
            List of detection dictionaries with keys:
                - class_name: Detected class name
                - confidence: Detection confidence
                - bbox: Bounding box [x1, y1, x2, y2]
                - center: Center point (x, y)
        """
        if self.model is None:
            logger.error("Model not loaded")
            return []
        
        try:
            # Run inference
            results = self.model(frame, verbose=False)[0]
            
            detections = []
            
            # Process each detection
            for box in results.boxes:
                confidence = float(box.conf[0])
                
                # Filter by confidence
                if confidence < self.confidence_threshold:
                    continue
                
                # Get class name
                class_id = int(box.cls[0])
                class_name = results.names[class_id]
                
                # Filter by target classes
                if class_name not in self.target_classes:
                    continue
                
                # Get bounding box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                bbox = [int(x1), int(y1), int(x2), int(y2)]
                
                # Calculate center
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                detection = {
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': bbox,
                    'center': (center_x, center_y)
                }
                
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        draw_confidence: bool = True
    ) -> np.ndarray:
        """
        Draw detection boxes on frame
        
        Args:
            frame: Input frame
            detections: List of detections
            draw_confidence: Whether to draw confidence scores
            
        Returns:
            Frame with drawn detections
        """
        frame_copy = frame.copy()
        
        for det in detections:
            bbox = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            
            # Color based on class type
            if class_name == 'person':
                color = (0, 0, 255)  # Red for humans
            elif class_name in ['dog', 'cat', 'bird']:
                color = (0, 165, 255)  # Orange for animals
            else:
                color = (0, 255, 255)  # Yellow for unidentified objects
            
            # Draw bounding box
            cv2.rectangle(
                frame_copy,
                (bbox[0], bbox[1]),
                (bbox[2], bbox[3]),
                color,
                2
            )
            
            # Draw label
            label = f"{class_name}"
            if draw_confidence:
                label += f" {confidence:.2f}"
            
            # Background for text
            (label_width, label_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
            )
            cv2.rectangle(
                frame_copy,
                (bbox[0], bbox[1] - label_height - 10),
                (bbox[0] + label_width, bbox[1]),
                color,
                -1
            )
            
            # Draw text
            cv2.putText(
                frame_copy,
                label,
                (bbox[0], bbox[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1
            )
        
        return frame_copy
    
    def classify_intrusion_type(self, detections: List[Dict]) -> str:
        """
        Classify type of intrusion
        
        Args:
            detections: List of detections
            
        Returns:
            Intrusion type: 'human', 'animal', 'object', or 'multiple'
        """
        if not detections:
            return 'none'
        
        class_names = [det['class_name'] for det in detections]
        
        has_human = 'person' in class_names
        has_animal = any(c in ['dog', 'cat', 'bird'] for c in class_names)
        has_object = any(c not in ['person', 'dog', 'cat', 'bird'] for c in class_names)
        
        types = []
        if has_human:
            types.append('human')
        if has_animal:
            types.append('animal')
        if has_object:
            types.append('object')
        
        if len(types) > 1:
            return 'multiple'
        elif types:
            return types[0]
        else:
            return 'unknown'
