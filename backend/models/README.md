# YOLO Models Directory

Place your YOLO model weights here.

## Downloading YOLO Models

### YOLOv8 (Recommended)

Download from Ultralytics:

```bash
# Activate your virtual environment first
.myenv\Scripts\activate

# Install ultralytics if not already installed
pip install ultralytics

# Download YOLOv8 nano model (fastest, smallest)
yolo task=detect mode=export model=yolov8n.pt format=pt
```

Or download manually from:
https://github.com/ultralytics/assets/releases

### Available Models

- **yolov8n.pt** - Nano (fastest, least accurate)
- **yolov8s.pt** - Small
- **yolov8m.pt** - Medium
- **yolov8l.pt** - Large
- **yolov8x.pt** - Extra Large (slowest, most accurate)

### Recommendation

For real-time performance on CPU, use **yolov8n.pt** or **yolov8s.pt**.

Update the model path in `config.yaml`:
```yaml
model:
  weights: "models/yolov8n.pt"
```
