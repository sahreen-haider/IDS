# Intrusion Detection System (IDS)

An intelligent intrusion detection system using YOLO object detection with Android smartphone as camera source.

## Features

- Real-time object detection using YOLO
- Android smartphone camera integration via IP Webcam
- Detection of:
  - Humans
  - Animals
  - Unidentified objects
- Alert system for intrusion events
- Configurable detection zones and sensitivity
- Logging and recording capabilities

## Prerequisites

- Python 3.8+
- Android smartphone with IP Webcam app or similar
- YOLO model weights

## Installation

1. Create and activate virtual environment:
```bash
python -m venv .myenv
.myenv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download YOLO weights:
   - Download YOLOv8 weights from [Ultralytics](https://github.com/ultralytics/ultralytics)
   - Place in `models/` directory

4. Configure the system:
   - Copy `config.yaml` and adjust settings
   - Set your Android phone IP address
   - Configure detection classes and alert preferences

## Android Camera Setup (IP Webcam)

1. Install the "IP Webcam" app on your Android phone (by Pavel Khlebovich).
2. Connect your phone and your Mac to the same Wi‑Fi network.
3. Open IP Webcam and start the server; note the IP shown (e.g., `http://192.168.1.100:8080`).
4. Use one of these endpoints in the config:
    - MJPEG stream: `http://<PHONE_IP>:8080/video` (preferred)
    - MJPEG stream (alt): `http://<PHONE_IP>:8080/video.mjpg`
    - Snapshot (JPEG): `http://<PHONE_IP>:8080/shot.jpg`
5. Update `camera.url` in [config.yaml](config.yaml) to the chosen endpoint.

Example:

```
camera:
   url: "http://192.168.1.100:8080/video"
   width: 1280
   height: 720
```

### Troubleshooting
- If the stream fails to open, try `video.mjpg` or `shot.jpg`.
- Ensure the app is running and both devices share the same network.
- Some networks block multicast; try another Wi‑Fi or mobile hotspot.
- Reduce resolution and FPS in the app if frames drop.

## Usage

Run the intrusion detection system:
```bash
python src/main.py
```

## Configuration

Edit `config.yaml` to customize:
- Camera source and resolution
- Detection confidence threshold
- Alert methods (email, sound, save)
- Detection classes to monitor

### Edge Computing Optimization

The system is optimized for edge devices (Raspberry Pi, embedded systems, etc.):

- **Frame Skip**: Process every Nth frame (`detection.frame_skip: 2`)
  - `1` = process every frame (slowest, most accurate)
  - `2` = process every 2nd frame (2x faster, recommended)
  - `3` = process every 3rd frame (3x faster)
  
- **Inference Size**: Smaller input size for YOLO (`detection.inference_size: 416`)
  - `640` = high quality, slower
  - `416` = balanced (recommended for edge)
  - `320` = fastest, lower accuracy
  
- **Resolution**: Camera resolution lowered to 640x480 for edge devices
  
- **Half Precision**: FP16 inference on GPU (`detection.use_half_precision: true`)

### Perimeter Zone Detection

Only trigger alerts when objects enter a defined perimeter zone:

- **Enable/Disable**: `detection.enable_perimeter: true`
- **Define Zone**: Set polygon points in normalized coordinates (0.0 to 1.0)
  ```yaml
  perimeter_zone:
    - [0.2, 0.3]   # Top-left (20% from left, 30% from top)
    - [0.8, 0.3]   # Top-right
    - [0.8, 0.9]   # Bottom-right
    - [0.2, 0.9]   # Bottom-left
  ```

**Zone Examples**:
- **Full frame**: `[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]`
- **Bottom half**: `[[0.0, 0.5], [1.0, 0.5], [1.0, 1.0], [0.0, 1.0]]`
- **Center zone**: `[[0.25, 0.25], [0.75, 0.25], [0.75, 0.75], [0.25, 0.75]]`
- **Doorway**: `[[0.3, 0.2], [0.7, 0.2], [0.7, 1.0], [0.3, 1.0]]`

The perimeter zone is visualized as a green overlay on the video feed.

## Project Structure

```
IDS/
├── src/
│   ├── main.py              # Entry point
│   ├── detector.py          # YOLO detection logic
│   ├── camera.py            # Camera handling
│   ├── alert_system.py      # Alert notifications
│   └── config.py            # Configuration loader
├── models/                  # YOLO model weights
├── data/                    # Captured images/videos
├── logs/                    # System logs
├── config.yaml              # Configuration file
└── requirements.txt         # Python dependencies
```

## License

MIT
