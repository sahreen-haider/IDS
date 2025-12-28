# IDS FastAPI Backend

Complete REST API and WebSocket streaming for the Intrusion Detection System.

## 🚀 Quick Start

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Run the Server

```bash
# From project root
python backend/main.py

# Or with uvicorn directly
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: **http://localhost:8000**

## 📡 API Endpoints

### System Control

#### Start Detection
```http
POST /api/detection/start
```

#### Stop Detection
```http
POST /api/detection/stop
```

#### Health Check
```http
GET /api/health
Response: {"status": "healthy", "detection_running": true, "camera_connected": true}
```

### Configuration

#### Get All Config
```http
GET /api/config/
Response: {camera: {...}, model: {...}, detection: {...}, alerts: {...}}
```

#### Update Camera Config
```http
PUT /api/config/camera
Body: {"url": "http://192.168.1.9:8080/video", "width": 640, "height": 480, "fps": 30}
```

#### Update Detection Config
```http
PUT /api/config/detection
Body: {"frame_skip": 2, "inference_size": 416, ...}
```

#### Update Perimeter Zone
```http
PUT /api/config/perimeter
Body: {"perimeter_zone": [[0.2, 0.3], [0.8, 0.3], [0.8, 0.9], [0.2, 0.9]], "enable": true}
```

### Alerts

#### Get Alert History
```http
GET /api/alerts/?limit=50&skip=0
Response: [{"id": "...", "timestamp": "...", "intrusion_type": "human", ...}, ...]
```

#### Get Latest Alert
```http
GET /api/alerts/latest
Response: {"id": "...", "timestamp": "...", "intrusion_type": "human", ...}
```

#### Delete Alert
```http
DELETE /api/alerts/{alert_id}
```

#### Clear All Alerts
```http
DELETE /api/alerts/
```

### Statistics

#### Get System Stats
```http
GET /api/stats/system
Response: {"fps": 30, "detection_fps": 15, "in_perimeter": 2, "outside_perimeter": 0}
```

#### Get Alert Stats
```http
GET /api/stats/alerts
Response: {"total_alerts": 10, "alerts_by_type": {"human": 7, "animal": 3}, "last_alert": "..."}
```

#### Get Current Detections
```http
GET /api/stats/detections
Response: {"detections": [...], "count": 2}
```

### Live Video Streaming

#### HTTP Stream (MJPEG)
```http
GET /api/live/stream
```
Returns continuous MJPEG stream. Use in `<img src="http://localhost:8000/api/live/stream">`

#### WebSocket Stream
```javascript
const ws = new WebSocket('ws://localhost:8000/api/live/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.frame - base64 encoded JPEG
  // data.stats - real-time statistics
  // data.detections - current detections
};
```

## 🏗️ Architecture

```
backend/
├── main.py                      # FastAPI app entry point
├── requirements.txt             # Python dependencies
│
├── api/                         # API endpoints
│   ├── config.py               # Configuration management
│   ├── alerts.py               # Alert history
│   ├── stats.py                # Statistics
│   ├── live.py                 # Video streaming
│   └── stream.py               # Deprecated (redirects to live)
│
└── src/                         # Core detection logic
    ├── detection_service.py    # Background detection thread
    ├── camera.py               # Camera handling
    ├── detector.py             # YOLO detection
    ├── alert_system.py         # Alert management
    ├── config.py               # Config loader
    └── main.py                 # Standalone CLI (legacy)
```

## 🔧 Features

- ✅ **Auto-start detection** - Starts on server startup
- ✅ **Background processing** - Runs in separate thread
- ✅ **Real-time streaming** - WebSocket + HTTP MJPEG
- ✅ **Live statistics** - FPS, detection counts, perimeter status
- ✅ **Hot config reload** - Update settings via API
- ✅ **Alert history** - JSON-based alert storage
- ✅ **CORS enabled** - Ready for frontend integration
- ✅ **Thread-safe** - Locks for shared data access

## 🌐 Remote Access

### Option 1: Cloudflare Tunnel (Recommended)
```bash
# Install cloudflared
# Then run:
cloudflared tunnel --url http://localhost:8000
```

### Option 2: ngrok
```bash
ngrok http 8000
```

### Option 3: Tailscale
- Install Tailscale on server and client
- Access via: `http://[tailscale-ip]:8000`

## 📊 Usage Examples

### Python Client
```python
import requests

# Start detection
requests.post("http://localhost:8000/api/detection/start")

# Get live stats
stats = requests.get("http://localhost:8000/api/stats/system").json()
print(f"FPS: {stats['fps']}, Detections: {stats['in_perimeter']}")

# Update perimeter
requests.put("http://localhost:8000/api/config/perimeter", json={
    "perimeter_zone": [[0.0, 0.5], [1.0, 0.5], [1.0, 1.0], [0.0, 1.0]],
    "enable": True
})
```

### JavaScript Client
```javascript
// Fetch stats
const stats = await fetch('http://localhost:8000/api/stats/system')
  .then(r => r.json());

// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/api/live/ws');
ws.onmessage = (event) => {
  const {frame, stats, detections} = JSON.parse(event.data);
  document.getElementById('video').src = `data:image/jpeg;base64,${frame}`;
};
```

## 🐛 Troubleshooting

### Port already in use
```bash
# Change port in main.py or run:
uvicorn backend.main:app --port 8001
```

### Camera connection failed
- Check camera URL in `shared/config.yaml`
- Ensure phone and server on same network
- Test camera URL in browser first

### Detection not starting
- Check logs in `backend/logs/ids.log`
- Verify YOLO model exists at `backend/models/yolov8n.pt`
- Check camera permissions

## 📝 API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Security Notes

For production:
1. Update CORS origins in `main.py`
2. Add authentication (JWT tokens)
3. Use HTTPS with SSL certificates
4. Rate limiting for API endpoints
5. Secure WebSocket connections (WSS)
