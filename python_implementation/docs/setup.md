# Environment Setup

## 1. Hardware
- Ubuntu PC (for dev)  
- Coral USB stick  
- 2× USB cameras  
- Zigbee module (e.g. XBee)

## 2. Software Prereqs
- Python 3.x  
- OpenCV  
- PyCoral runtime  
- Zigbee library (e.g. `pyserial`, `zigpy`)

## 3. Installation Steps
1. Create & activate venv  
2. `pip install -r requirements.txt`  
3. Install Coral drivers  
4. Configure Zigbee serial port

## Python Environment (Conda)

- Create environment: `conda env create -f environment.yml`
- Activate: `conda activate smart_office_security_v2`
- Install Coral USB drivers (see pycoral docs)

## Running

- Run: `python src/main.py --model_tpu <path> --model_cpu <path> [--headless]`