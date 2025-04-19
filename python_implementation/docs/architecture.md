# System Architecture

## 1. High‑Level Diagram
- Camera → Preprocessing → Inference (TPU/CPU) → Display + Logging → Zigbee

## 2. Components
- Camera capture (2 USB @ 640×480, resize to 300×300)  
- TPU inference (Coral USB)  
- CPU fallback  
- Display windows & FPS overlay  
- Console logger  
- Zigbee sender

## 3. Data & Control Flow
- Frame scheduling @20 FPS  
- Fallback trigger logic  
- Event payload format

## Python Implementation (Beta)

- `/src/main.py`: Orchestrates camera streams, inference, display, logging, Zigbee
- `/src/camera.py`: Threaded USB camera capture (640x480)
- `/src/inference.py`: Mobilenet SSD inference (TPU/CPU fallback)
- `/src/display.py`: Bounding box + FPS overlay (two windows)
- `/src/logger.py`: Console output for detections
- `/src/zigbee.py`: Serial event sender

Fallback logic: If TPU inference fails, CPU inference is used automatically.

Headless mode: Use `--headless` CLI flag.