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

## 4. Building Receiving Applications (Conceptual)

*(This section remains largely the same, outlining how to build clients for alerts, logs, and video.)*

*   **Alert Notification:** Subscribe to `.../alert`, trigger OS notification.
*   **Detection Log Saving:** Subscribe to `.../detection_log`, parse JSON, generate timestamped filename, save JSON string.
*   **Video Stream Display:** Subscribe to `.../0/stream` and `.../1/stream`, decode JPEG bytes using OpenCV (`cv2.imdecode`), display in separate `cv2.imshow` windows.

## 5. Running the System (End-to-End Example)

This section provides a step-by-step guide to run the system, assuming the broker (Section 1) and Pi dependencies (Section 2) are set up.

**On the Raspberry Pi:**

1.  **SSH into the Raspberry Pi:**
    ```bash
    ssh pi@<PI_IP_ADDRESS>
    ```
    (Replace `<PI_IP_ADDRESS>` with your Pi's actual IP address)

2.  **Navigate to the Project Directory:**
    ```bash
    cd path/to/smart_office_security_v2/python_implementation
    ```
    (Adjust the path as necessary)

3.  **Run the Main Application:**
    ```bash
    python3 src/main.py --mqtt-broker <MAIN_COMPUTER_IP> --cam0 <CAM0_INDEX> --cam1 <CAM1_INDEX>
    ```
    *   Replace `<MAIN_COMPUTER_IP>` with the IP address of the computer running the Mosquitto broker (e.g., `192.168.5.135`).
    *   Replace `<CAM0_INDEX>` and `<CAM1_INDEX>` with the correct video device indices for your cameras (e.g., `0` and `2`).
    *   Add `--headless` if you don't want local display windows on the Pi itself.

    The Pi should now connect to the MQTT broker and start sending alerts, logs (after 5s inactivity following detections), and continuous video streams.

**On the Main Computer:**

You need separate processes (terminals or a dedicated script) to listen for the different MQTT topics.

1.  **Ensure Mosquitto Broker is Running:** (See Section 1)

2.  **Listen for Alerts (Terminal 1):**
    Open a terminal and run:
    ```bash
    mosquitto_sub -h localhost -t smart_office/camera/alert -v
    ```
    (Replace `localhost` with the broker IP if not running `mosquitto_sub` on the broker machine itself). You will see alert messages printed here when the Pi detects a person.
    *For actual pop-up notifications, you would need a script using a library like `plyer` (Python) or `notify-send` (Linux).* 

3.  **Listen for Detection Logs (Terminal 2):**
    Open another terminal and run:
    ```bash
    mosquitto_sub -h localhost -t smart_office/camera/detection_log > detection_log_output.txt
    ```
    This will print the raw JSON log data to the console (and optionally redirect to a file). 
    *To save logs as individual timestamped JSON files, you need a script that subscribes, parses the JSON to find a timestamp (like `detection_period_end`), formats it (e.g., `YYYY-MM-DD-HH-MM-SS.json`), and saves the received JSON string.* 

4.  **Display Video Streams (Python Script):**
    You need a Python script to receive and display the video streams. Here is a basic example concept (`mqtt_video_viewer.py`):

    ```python
    # mqtt_video_viewer.py
    import cv2
    import paho.mqtt.client as mqtt
    import numpy as np

    MQTT_BROKER = "localhost" # Or your broker IP
    MQTT_PORT = 1883
    TOPIC_STREAM_0 = "smart_office/camera/0/stream"
    TOPIC_STREAM_1 = "smart_office/camera/1/stream"

    def on_connect(client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe([(TOPIC_STREAM_0, 0), (TOPIC_STREAM_1, 0)])

    def on_message(client, userdata, msg):
        try:
            # Decode the JPEG image bytes
            nparr = np.frombuffer(msg.payload, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                window_name = "Camera 0 Stream" if msg.topic == TOPIC_STREAM_0 else "Camera 1 Stream"
                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): # Allow quitting by pressing 'q'
                    client.disconnect()
                    cv2.destroyAllWindows()
            else:
                print(f"Failed to decode frame from topic {msg.topic}")
        except Exception as e:
            print(f"Error processing message on {msg.topic}: {e}")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Create windows beforehand
    cv2.namedWindow("Camera 0 Stream", cv2.WINDOW_NORMAL)
    cv2.namedWindow("Camera 1 Stream", cv2.WINDOW_NORMAL)

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Disconnecting...")
        client.disconnect()
        cv2.destroyAllWindows()
    ```
    Save this script (e.g., as `mqtt_video_viewer.py`) on your main computer, ensure you have `opencv-python` and `paho-mqtt` installed (`pip install opencv-python paho-mqtt`), and run it:
    ```bash
    python mqtt_video_viewer.py
    ```
    This script will open two windows displaying the live, annotated video streams from the Pi.

**Expected Outcome:**

*   The Pi runs `main.py`, performing inference and sending data via MQTT.
*   On the main computer:
    *   Terminal 1 shows incoming alert messages.
    *   Terminal 2 shows incoming JSON log data.
    *   The `mqtt_video_viewer.py` script shows two windows with the live, annotated camera feeds.
    *   *(Actual notification pop-ups and individual JSON file saving require dedicated scripts as described)*. 