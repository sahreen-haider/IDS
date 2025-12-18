"""
Main entry point for Intrusion Detection System
"""
import cv2
import logging
import sys
import time
from pathlib import Path

from config import Config
from camera import CameraHandler
from detector import IntrusionDetector
from alert_system import AlertSystem


def setup_logging(log_level: str = "INFO", log_file: str = "logs/ids.log"):
    """Setup logging configuration"""
    # Create logs directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main function to run the IDS"""
    print("=" * 60)
    print("Intrusion Detection System - Starting...")
    print("=" * 60)
    
    # Load configuration
    try:
        config = Config("config.yaml")
        print("✓ Configuration loaded")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return
    
    # Setup logging
    setup_logging(
        log_level=config.get('logging.level', 'INFO'),
        log_file=config.get('logging.file', 'logs/ids.log')
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Intrusion Detection System initialized")
    
    # Initialize camera
    camera = CameraHandler(
        camera_url=config.camera_url,
        width=config.camera_width,
        height=config.camera_height
    )
    
    if not camera.connect():
        logger.error("Failed to connect to camera. Check your configuration.")
        print("✗ Camera connection failed")
        print("\nTroubleshooting:")
        print("1. Ensure Android phone IP Webcam app is running")
        print("2. Check the IP address in config.yaml")
        print("3. Make sure your computer and phone are on the same network")
        return
    
    print("✓ Camera connected")
    logger.info(f"Camera resolution: {camera.get_resolution()}")
    
    # Initialize detector
    detector = IntrusionDetector(
        model_path=config.model_weights,
        target_classes=config.target_classes,
        confidence_threshold=config.confidence_threshold,
        device=config.get('model.device', 'cpu')
    )
    
    if not detector.load_model():
        logger.error("Failed to load YOLO model")
        print("✗ Model loading failed")
        print("\nTroubleshooting:")
        print("1. Download YOLO weights and place in models/ directory")
        print("2. Check model path in config.yaml")
        camera.release()
        return
    
    print("✓ YOLO model loaded")
    
    # Initialize alert system
    alert_system = AlertSystem(
        save_path=config.get('alerts.save_path', 'data/detections'),
        alert_cooldown=config.alert_cooldown,
        enable_sound=config.get('alerts.sound', True),
        enable_save=config.get('alerts.save_image', True)
    )
    
    print("✓ Alert system initialized")
    print("\n" + "=" * 60)
    print("System ready - Monitoring for intrusions...")
    print("Press 'q' to quit, 's' to show statistics")
    print("=" * 60 + "\n")
    
    # Main detection loop
    frame_count = 0
    fps_start_time = time.time()
    fps = 0
    
    try:
        while True:
            # Read frame
            ret, frame = camera.read_frame()
            if not ret:
                logger.warning("Failed to read frame, retrying...")
                time.sleep(0.1)
                continue
            
            # Perform detection
            detections = detector.detect(frame)
            
            # Check for intrusions
            if detections:
                intrusion_type = detector.classify_intrusion_type(detections)
                alert_triggered = alert_system.trigger_alert(
                    frame, detections, intrusion_type
                )
                
                if alert_triggered:
                    print(f"⚠️  ALERT: {intrusion_type.upper()} intrusion detected!")
            
            # Draw detections on frame
            if config.get('display.draw_boxes', True):
                frame = detector.draw_detections(
                    frame,
                    detections,
                    draw_confidence=config.get('display.draw_confidence', True)
                )
            
            # Calculate FPS
            frame_count += 1
            if frame_count >= 30:
                fps = frame_count / (time.time() - fps_start_time)
                frame_count = 0
                fps_start_time = time.time()
            
            # Draw FPS and status
            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            if detections:
                status_text = f"INTRUSION: {len(detections)} object(s)"
                color = (0, 0, 255)
            else:
                status_text = "STATUS: Monitoring"
                color = (0, 255, 0)
            
            cv2.putText(
                frame,
                status_text,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )
            
            # Display frame
            if config.show_window:
                window_name = config.get('display.window_name', 'IDS')
                cv2.imshow(window_name, frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nShutting down...")
                break
            elif key == ord('s'):
                stats = alert_system.get_statistics()
                print("\n" + "=" * 40)
                print("STATISTICS")
                print("=" * 40)
                print(f"Total alerts: {stats['total_alerts']}")
                print(f"Alerts by type: {stats['alerts_by_type']}")
                print(f"Last alert: {stats['last_alert']}")
                print("=" * 40 + "\n")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
    
    finally:
        # Cleanup
        camera.release()
        cv2.destroyAllWindows()
        
        # Show final statistics
        stats = alert_system.get_statistics()
        print("\n" + "=" * 60)
        print("FINAL STATISTICS")
        print("=" * 60)
        print(f"Total alerts: {stats['total_alerts']}")
        print(f"Alerts by type: {stats['alerts_by_type']}")
        print("=" * 60)
        
        logger.info("Intrusion Detection System stopped")
        print("\nSystem stopped successfully")


if __name__ == "__main__":
    main()
