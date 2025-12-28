"""
Quick test script for FastAPI backend
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing FastAPI Backend Setup...")
print("=" * 60)

# Test 1: Import main modules
print("\n1. Testing imports...")
try:
    from backend.main import app
    print("   ✓ FastAPI app imported")
except Exception as e:
    print(f"   ✗ Failed to import app: {e}")
    sys.exit(1)

try:
    from backend.api import config, alerts, stats, live
    print("   ✓ API modules imported")
except Exception as e:
    print(f"   ✗ Failed to import API modules: {e}")
    sys.exit(1)

try:
    from backend.src import DetectionService
    print("   ✓ DetectionService imported")
except Exception as e:
    print(f"   ✗ Failed to import DetectionService: {e}")
    sys.exit(1)

# Test 2: Check FastAPI routes
print("\n2. Checking API routes...")
routes = [route.path for route in app.routes]
expected_routes = [
    '/api/config/',
    '/api/alerts/',
    '/api/stats/system',
    '/api/live/stream',
    '/api/detection/start',
    '/api/detection/stop'
]

for route in expected_routes:
    if any(route in r for r in routes):
        print(f"   ✓ {route}")
    else:
        print(f"   ✗ {route} - NOT FOUND")

# Test 3: Check config file
print("\n3. Checking configuration...")
try:
    import yaml
    with open('shared/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print(f"   ✓ Config loaded")
    print(f"   ✓ Camera: {config['camera']['url']}")
    print(f"   ✓ Perimeter: {'enabled' if config['detection']['enable_perimeter'] else 'disabled'}")
except Exception as e:
    print(f"   ✗ Config error: {e}")

# Test 4: Check model file
print("\n4. Checking YOLO model...")
model_path = "backend/models/yolov8n.pt"
if os.path.exists(model_path):
    print(f"   ✓ Model found at {model_path}")
else:
    print(f"   ✗ Model NOT found at {model_path}")
    print(f"   ! Download YOLOv8n weights and place in backend/models/")

print("\n" + "=" * 60)
print("Setup test complete!")
print("\nTo start the server:")
print("  python backend/main.py")
print("\nOr with uvicorn:")
print("  uvicorn backend.main:app --reload")
print("\nAPI will be available at: http://localhost:8000")
print("API docs at: http://localhost:8000/docs")
print("=" * 60)
