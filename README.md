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
