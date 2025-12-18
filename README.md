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

## Android Camera Setup

1. Install IP Webcam app on your Android phone
2. Start the server in the app
3. Note the IP address (e.g., http://192.168.1.100:8080)
4. Update the `camera_url` in `config.yaml`

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
