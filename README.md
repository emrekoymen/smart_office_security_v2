# Smart Office Security - Python Person Detection Module

This document describes the Python implementation for person detection within the Smart Office Security project.

## 1. Project Overview

The Python module is responsible for real-time person detection using connected cameras.

-   **Objective**: Detect individuals in designated office areas using video feeds.
-   **Key features**:
    -   Dual-camera support for comprehensive coverage.
    -   Utilizes Coral Edge TPU for accelerated inference, with CPU fallback.
    -   MQTT for real-time alerts and data streaming.

## 2. Quick Start

### Prerequisites

-   Ubuntu (or a similar Debian-based Linux distribution)
-   Python 3.x (Python 3.9 recommended for Raspberry Pi deployment, see specific guide)
-   Conda (for environment management on development machines)

### Installation and Setup

1.  **Clone the repository (if you haven't already):**
    ```bash
    # git clone <your-repository-url>
    # cd <repository-name>
    ```

2.  **Navigate to the Python implementation directory:**
    ```bash
    cd python_implementation
    ```

3.  **Create and activate the Conda environment:**
    ```bash
    conda env create -f environment.yml
    conda activate smart_office_security_v2
    ```

4.  **Install PyCoral:**
    (Ensure your Conda environment is activated)
    ```bash
    python -m pip install --extra-index-url https://google-coral.github.io/py-repo/ pycoral~=2.0
    ```

### Running the Application

From within the `python_implementation/src/` directory:

-   **With display (shows camera feeds and detections):**
    ```bash
    python main.py --camera-ids 0 1 # Adjust camera IDs as needed
    ```
-   **Headless mode (no GUI, for background operation):**
    ```bash
    python main.py --camera-ids 0 1 --headless
    ```

## 3. Repository Structure (Python Module)

The core Python code is located within the `python_implementation` directory:

-   `python_implementation/src/`: Main source code for the detection application.
-   `python_implementation/models/`: Contains the machine learning models (e.g., `.tflite` files).
-   `python_implementation/docs/`: Detailed documentation, including architecture and development notes.
-   `python_implementation/requirements.txt`: Pip requirements (primarily for reference or non-Conda setups).
-   `python_implementation/environment.yml`: Conda environment definition.
-   `python_implementation/RASPBERRY_PI_INTEGRATION.md`: Detailed guide for deploying on Raspberry Pi.

## 4. CLI Usage

The main script (`python_implementation/src/main.py`) accepts the following arguments:

-   `--headless`: Run the application without displaying camera feeds or GUI elements.
-   `--camera-ids`: A list of camera indices to use (e.g., `0 1` for `/dev/video0` and `/dev/video1`).

## 5. System Architecture (Python Module)

### High-Level Diagram

Camera Feeds → Frame Preprocessing → Inference (TPU/CPU) → Detection Logging, Alerting & Streaming via MQTT

### Components

-   **Camera Capture**: Utilizes OpenCV to capture frames from multiple USB cameras (default 640x480, resized for model input).
-   **TPU Inference**: Leverages the Coral USB Accelerator for fast person detection using a MobileNet SSD model.
-   **CPU Fallback**: If a Coral TPU is not available or encounters issues, inference can fall back to using the CPU (slower performance).
-   **Display**: Real-time display of camera feeds with bounding boxes around detected persons and FPS overlay (if not in headless mode).
-   **MQTT Publisher**: Sends alerts, detailed detection logs, and annotated video streams to an MQTT broker.
-   **Console Logger**: Outputs detection events and system status to the console.

### Data & Control Flow

-   Frames are scheduled from cameras at approximately 20 FPS.
-   Logic is in place to trigger CPU fallback if TPU inference fails.
-   Alerts, logs, and video stream data are published to designated MQTT topics.

For more details, refer to `python_implementation/docs/architecture.md`.

## 6. Raspberry Pi Deployment

For instructions on deploying this Python module to a Raspberry Pi 4, including Coral USB Accelerator setup and running as a service, please see the dedicated guide:
[Raspberry Pi 4 Deployment Guide](./python_implementation/RASPBERRY_PI_INTEGRATION.md)

## 7. Roadmap & Next Steps (for Python Module)

-   Further optimization for embedded platforms.
-   Enhanced error handling and recovery.
-   Integration with a broader smart office system.

*(Note: A C++ implementation is also part of the larger Smart Office Security project, located in the `cpp_implementation` directory.)* 