# Development Guide

## 1. Coding Style & Conventions
- Python best practices  
- Module layout

## 2. Module Breakdown
- `camera.py` – capture & resize  
- `inference.py` – TPU & CPU engine  
- `display.py` – window management & overlay  
- `logger.py` – console output  
- `zigbee.py` – event transmission

## 3. Python Modules

- `camera.py`: CameraStream class (threaded capture)
- `inference.py`: PersonDetector (TPU/CPU fallback)
- `display.py`: DisplayWindow (bbox, FPS)
- `logger.py`: log_person_detected
- `zigbee.py`: ZigbeeSender (serial)
- `main.py`: CLI, orchestration

### CLI Flags
- `--headless`, `--cam0`, `--cam1`, `--model_tpu`, `--model_cpu`, `--zigbee_port`, `--threshold`

## 4. CLI Flags
- `--headless`  
- logging verbosity  
- camera indices

## 5. Testing Locally
- Simulated feeds  
- CPU‑only mode switch