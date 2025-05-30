# MQTT Integration Guide for Smart Office Security

This document explains how the Python application uses MQTT for communication and how to set up the necessary components on the main computer (broker) and receiving clients.

## 1. MQTT Broker Setup (Main Computer)

You need an MQTT broker running on the main computer. Mosquitto is a popular and lightweight option.

**Installation:**

*   **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt update
    sudo apt install mosquitto mosquitto-clients
    sudo systemctl enable mosquitto
    sudo systemctl start mosquitto
    ```
*   **macOS:**
    ```bash
    brew install mosquitto
    # Start manually or configure launchd
    brew services start mosquitto
    ```
*   **Windows:** Download from the [Mosquitto website](https://mosquitto.org/download/). Run the installer and ensure the service is started.

**Verification:**
Check if the broker is running (usually on port 1883):
```bash
netstat -tulnp | grep 1883 # Linux
# Or use systemctl status mosquitto
```

## 2. Python Application (Raspberry Pi)

The Python script (`python_implementation/src/main.py`) acts as an MQTT client.

**Dependencies:** Ensure `paho-mqtt` and other dependencies are installed on the Pi:
```bash
# SSH into the Pi first
cd path/to/smart_office_security_v2 # Navigate to your project directory
pip install -r python_implementation/requirements.txt
# ALSO ensure tflite_runtime is installed correctly for your Pi/Coral device
# See: https://coral.ai/docs/accelerator/get-started/#installation
```

## 3. MQTT Communication Topics

The application uses the following MQTT topics:

*   `smart_office/camera/alert`: Person detection alerts (Text)
*   `smart_office/camera/detection_log`: Buffered detection events (JSON)
*   `smart_office/camera/0/stream`: Annotated video stream from Camera 0 (JPEG Bytes)
*   `smart_office/camera/1/stream`: Annotated video stream from Camera 1 (JPEG Bytes)

*(Payload details omitted for brevity - see previous sections)*

## 4. Main Computer Listener Scripts

In the `python_implementation/main_computer_listeners/` directory, you'll find dedicated Python scripts to receive and process data from the Raspberry Pi:
*   `video_viewer.py`: Displays the camera streams.
*   `alert_listener.py`: Listens for and shows alerts.
*   `log_saver.py`: Saves detection logs to JSON files.

**Dependencies for Listener Scripts:**
On your main computer, navigate to this directory and install its requirements:
```bash
cd path/to/smart_office_security_v2/python_implementation/main_computer_listeners
pip install -r requirements.txt
# If you want desktop notifications in alert_listener.py, also: pip install plyer
```

## 5. Running the System (End-to-End Example)

This section provides a step-by-step guide to run the system.

**Prerequisites:**
1.  MQTT Broker is installed and running on the main computer (Section 1).
2.  Raspberry Pi application dependencies are installed (Section 2).
3.  Main computer listener script dependencies are installed (Section 4).

**A. On the Raspberry Pi:**

1.  **SSH into the Raspberry Pi:**
    ```bash
    ssh pi@<PI_IP_ADDRESS>
    ```
    (Replace `<PI_IP_ADDRESS>` with your Pi's actual IP address)

2.  **Navigate to the Project Directory:**
    ```bash
    cd path/to/smart_office_security_v2/python_implementation
    ```
    (Adjust `path/to/` as necessary)

3.  **Run the Main Application:**
    ```bash
    python3 src/main.py --mqtt-broker <MAIN_COMPUTER_IP> --cam0 <CAM0_INDEX> --cam1 <CAM1_INDEX>
    ```
    *   Replace `<MAIN_COMPUTER_IP>` with the IP address of your main computer (e.g., `192.168.5.135`).
    *   Replace `<CAM0_INDEX>` and `<CAM1_INDEX>` with your camera indices (e.g., `0` and `2`).
    *   Add `--headless` if you don't want local display windows on the Pi itself.

    The Pi will connect to the MQTT broker and start sending data.

**B. On the Main Computer:**

You need to run each of the listener scripts in separate terminal windows.
First, navigate to the listeners directory in each terminal:
```bash
cd path/to/smart_office_security_v2/python_implementation/main_computer_listeners
```
(Adjust `path/to/` as necessary)

1.  **Run the Alert Listener (Terminal 1):**
    ```bash
    python3 alert_listener.py --mqtt-broker <MAIN_COMPUTER_IP>
    ```
    *   Replace `<MAIN_COMPUTER_IP>` with your main computer's IP (or `localhost` if running the broker on the same machine).
    *   Alerts will be printed to the console. For pop-up notifications, you'd modify the script to use a library like `plyer`.

2.  **Run the Log Saver (Terminal 2):**
    ```bash
    python3 log_saver.py --mqtt-broker <MAIN_COMPUTER_IP>
    ```
    *   Replace `<MAIN_COMPUTER_IP>` as above.
    *   Detection logs will be saved as timestamped JSON files in a `detection_logs` subdirectory (created automatically).

3.  **Run the Video Viewer (Terminal 3):**
    ```bash
    python3 video_viewer.py --mqtt-broker <MAIN_COMPUTER_IP>
    ```
    *   Replace `<MAIN_COMPUTER_IP>` as above.
    *   Two OpenCV windows will open, displaying the live (grayscale) annotated video streams from "Camera 0 Stream" and "Camera 1 Stream". Press 'q' in one of these windows to close the viewer.

**Expected Outcome:**

*   The Raspberry Pi runs `src/main.py`, performing inference and sending processed grayscale frames, alerts, and log data via MQTT.
*   On the main computer:
    *   Terminal 1 (running `alert_listener.py`) shows incoming alert messages.
    *   Terminal 2 (running `log_saver.py`) announces saved log files in the `detection_logs` directory.
    *   Terminal 3 (running `video_viewer.py`) shows two windows with the live, annotated grayscale camera feeds.

This setup provides the complete pipeline as requested. 