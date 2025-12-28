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
        device: str = 'cpu',
        inference_size: int = 416,
        use_half: bool = False,
        perimeter_zone: List[List[float]] = None
    ):
        """
        Initialize intrusion detector
        
        Args:
            model_path: Path to YOLO model weights
            target_classes: List of class names to detect
            confidence_threshold: Minimum confidence for detection
            device: Device to run inference on ('cpu', 'cuda', 'mps')
            inference_size: Image size for inference (smaller = faster)
            use_half: Use half precision (FP16) for faster inference
            perimeter_zone: List of normalized zone points [[x1,y1], [x2,y2], ...]
        """
        self.model_path = model_path
        self.target_classes = target_classes
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.inference_size = inference_size
        self.use_half = use_half
        self.model = None
        self.perimeter_zone = perimeter_zone or [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
        self.perimeter_pixels = None  # Will be set when frame size is known
        
    def set_perimeter_pixels(self, frame_width: int, frame_height: int):
        """
        Convert normalized perimeter coordinates to pixel coordinates
        
        Args:
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
        """
        self.perimeter_pixels = np.array([
            [int(x * frame_width), int(y * frame_height)] 
            for x, y in self.perimeter_zone
        ], dtype=np.int32)
        logger.info(f"Perimeter zone set: {len(self.perimeter_zone)} points")
    
    def is_point_in_perimeter(self, point: Tuple[int, int]) -> bool:
        """
        Check if a point is inside the perimeter zone
        
        Args:
            point: (x, y) coordinates
            
        Returns:
            True if point is inside perimeter, False otherwise
        """
        if self.perimeter_pixels is None:
            return True  # No perimeter set, allow all
        
        # Use OpenCV's pointPolygonTest
        result = cv2.pointPolygonTest(self.perimeter_pixels, point, False)
        return result >= 0  # >= 0 means inside or on boundary
    
    def is_detection_in_perimeter(self, detection: Dict) -> bool:
        """
        Check if detection is inside the perimeter zone
        
        Args:
            detection: Detection dictionary with 'center' and 'bbox'
            
        Returns:
            True if detection is inside perimeter, False otherwise
        """
        center = detection['center']
        return self.is_point_in_perimeter(center)
    
    def filter_detections_by_perimeter(self, detections: List[Dict]) -> List[Dict]:
        """
        Filter detections to only include those inside perimeter
        
        Args:
            detections: List of all detections
            
        Returns:
            List of detections inside perimeter
        """
        if self.perimeter_pixels is None:
            return detections  # No filtering if no perimeter
        
        return [det for det in detections if self.is_detection_in_perimeter(det)]
    
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
            
            # Apply edge optimizations
            if self.use_half and self.device != 'cpu':
                self.model.half()  # FP16 only works on GPU
                logger.info("Half precision (FP16) enabled")
            
            logger.info(f"Model loaded successfully on {self.device}")
            logger.info(f"Inference size: {self.inference_size}x{self.inference_size}")
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
            # Run inference with optimized image size
            results = self.model(frame, imgsz=self.inference_size, verbose=False)[0]
            
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
    
    def draw_perimeter_zone(self, frame: np.ndarray, color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """
        Draw perimeter zone on frame
        
        Args:
            frame: Input frame
            color: Zone line color (BGR)
            thickness: Line thickness
            
        Returns:
            Frame with drawn perimeter
        """
        if self.perimeter_pixels is None:
            return frame
        
        # Draw semi-transparent overlay
        overlay = frame.copy()
        cv2.polylines(overlay, [self.perimeter_pixels], isClosed=True, color=color, thickness=thickness)
        cv2.fillPoly(overlay, [self.perimeter_pixels], color=color)
        
        # Blend with original frame (20% opacity for fill)
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        
        # Draw solid border
        cv2.polylines(frame, [self.perimeter_pixels], isClosed=True, color=color, thickness=thickness)
        
        # Add label
        cv2.putText(frame, "PERIMETER ZONE", (10, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return frame
    
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
