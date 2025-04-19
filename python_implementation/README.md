# Smart Office Person Detection

## 1. Project Overview
- Objective  
- Key features (dual‑camera, TPU+CPU fallback, Zigbee)

## 2. Quick Start
- Prereqs (Ubuntu, Python 3.x)
- Install deps 
  ```bash
  conda env create -f environment.yml
  conda activate smart_office_security_v2
  python -m pip install --extra-index-url https://google-coral.github.io/py-repo/ pycoral~=2.0
  ```
- Run in “display” vs “headless” mode

## 3. Repository Structure
- `/src`  
- `/models`  
- `/docs`

## 4. CLI Usage
- `--headless`  
- `--camera-ids`

## 5. Roadmap & Next Steps
- C++ port  
- Raspberry Pi deploy# System Architecture

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
- Event payload format# Smart Office Person Detection

## 1. Project Overview
- Objective  
- Key features (dual‑camera, TPU+CPU fallback, Zigbee)

## 2. Quick Start
- Prereqs (Ubuntu, Python 3.x)
- Install deps 
  ```bash
  conda env create -f environment.yml
  conda activate smart_office_security_v2
  python -m pip install --extra-index-url https://google-coral.github.io/py-repo/ pycoral~=2.0
  ```
- Run in “display” vs “headless” mode

## 3. Repository Structure
- `/src`  
- `/models`  
- `/docs`

## 4. CLI Usage
- `--headless`  
- `--camera-ids`

## 5. Roadmap & Next Steps
- C++ port  
- Raspberry Pi deploy

## Python Implementation (Beta)

- Initial Python codebase implemented in `/src/`:
  - Dual USB camera capture with OpenCV
  - Mobilenet SSD inference using Coral Edge TPU with CPU fallback
  - Real-time display with bounding boxes and FPS overlay (two windows)
  - Console logging: `Person Detected! (Confidence Score: X)`
  - Zigbee event transmission (timestamp, confidence, bbox)
  - CLI flag for headless mode
- Conda environment setup via `environment.yml`

See `docs/architecture.md` and `docs/development.md` for details.