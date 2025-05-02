# Raspberry Pi 4 Deployment Guide for Smart Office Person Detection

This guide details the steps to set up and run the Python implementation of the Smart Office Person Detection project on a Raspberry Pi 4.

## 1. Prerequisites

*   **Hardware:**
    *   Raspberry Pi 4 Model B (2GB RAM or more recommended)
    *   Coral USB Accelerator
    *   USB Cameras (compatible with the Pi)
    *   Power supply, SD card, etc.
*   **Software:**
    *   Raspberry Pi OS (Legacy 32-bit or 64-bit recommended for better compatibility, especially Python 3.9). Check PyCoral/TensorFlow Lite requirements if using newer OS versions.
    *   Python 3.9 (Verify with `python3 --version`. If you have a different version, consider using `pyenv` to install and manage Python 3.9, or use an OS version that includes it).
    *   Internet connection.

## 2. Initial Raspberry Pi Setup

1.  **Install Raspberry Pi OS:** Flash your SD card with Raspberry Pi OS.
2.  **Boot and Configure:** Complete the initial setup wizard (language, timezone, Wi-Fi, etc.).
3.  **Update System:** Open a terminal and run:
    ```bash
    sudo apt update
    sudo apt full-upgrade -y
    sudo reboot
    ```
4.  **Enable Camera (if using Pi Camera):** Run `sudo raspi-config`, navigate to `Interface Options` -> `Legacy Camera`, and enable it. Reboot if prompted. (This project uses USB cameras, so this might not be needed).
5.  **Install `git` (if not present):**
    ```bash
    sudo apt install git -y
    ```

## 3. Install Coral Edge TPU Runtime

Follow the official Coral documentation for installing the Edge TPU runtime on Linux (Debian-based systems):

1.  **Add Coral Package Repository:**
    ```bash
    echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
    sudo apt update
    ```
2.  **Install Edge TPU Runtime:**
    *   For standard frequency (recommended):
        ```bash
        sudo apt install libedgetpu1-std -y
        ```
    *   *Optional:* For maximum frequency (higher performance, more heat):
        ```bash
        # sudo apt install libedgetpu1-max -y
        ```
3.  **Connect Coral USB Accelerator:** Plug it into a USB 3.0 port on the Raspberry Pi **after** installing the runtime. If already plugged in, unplug and replug it.

## 4. Set Up Python Environment and Dependencies

Using `conda` on Raspberry Pi can be problematic. We recommend using Python's built-in `venv` module.

1.  **Install Python `venv` module (usually included, but just in case):**
    ```bash
    sudo apt install python3-venv -y
    ```
2.  **Clone the Project Repository:**
    ```bash
    # Navigate to your desired projects directory, e.g., /home/pi/projects
    # mkdir -p ~/projects && cd ~/projects
    git clone <your-repository-url> smart_office_security_v2
    cd smart_office_security_v2/python_implementation
    ```
3.  **Create and Activate a Virtual Environment:** (Ensure you are running this with Python 3.9)
    ```bash
    python3.9 -m venv .venv
    source .venv/bin/activate
    # Your prompt should now start with (.venv)
    ```
4.  **Upgrade `pip`:**
    ```bash
    pip install --upgrade pip
    ```
5.  **Install System Dependencies for OpenCV:** OpenCV often requires system libraries. Install common ones:
    ```bash
    sudo apt install -y build-essential cmake pkg-config libjpeg-dev libpng-dev libtiff-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libgtk-3-dev libatlas-base-dev gfortran python3-dev libhdf5-dev libhdf5-serial-dev libhdf5-103
    ```
    *(Note: Some of these might already be installed or unnecessary depending on the exact OpenCV version `pip` installs, but it's safer to include them).*
6.  **Install Python Packages:**
    *   Install `pycoral` via `apt` (recommended if using Python 3.9 and compatible OS):
        ```bash
        sudo apt install python3-pycoral -y
        ```
        *(If this fails or you're not using Python 3.9, check Coral docs/GitHub issues for alternative methods, like installing specific wheels or using Docker).*
    *   Install `tflite-runtime`: Find the correct wheel (`.whl`) file for your Pi's architecture (e.g., `linux_armv7l` for 32-bit OS, `linux_aarch64` for 64-bit OS) and Python version (cp39 for Python 3.9) from [tensorflow.org/lite/guide/python](https://www.tensorflow.org/lite/guide/python) or related Google repositories. Download it and install using pip:
        ```bash
        # Example for Pi 4 64-bit OS with Python 3.9 (find the correct URL/filename)
        # wget https://dl.google.com/coral/python/tflite_runtime-2.5.0.post1-cp39-cp39-linux_aarch64.whl
        # pip install tflite_runtime-2.5.0.post1-cp39-cp39-linux_aarch64.whl
        # Replace with the actual correct wheel file for your setup!
        ```
    *   Install other dependencies using `pip`:
        ```bash
        pip install "numpy<2.0" opencv-python pyserial imutils
        # Or use opencv-python-headless if you don't need GUI windows on the Pi:
        # pip install "numpy<2.0" opencv-python-headless pyserial imutils
        ```

## 5. Running the Application

1.  **Ensure Virtual Environment is Active:** If not, navigate to `python_implementation` and run `source .venv/bin/activate`.
2.  **Connect Cameras:** Ensure your USB cameras are connected. You might need to identify their IDs (e.g., `/dev/video0`, `/dev/video2`). You can try listing devices with `ls /dev/video*`.
3.  **Navigate to Source Directory:**
    ```bash
    cd src
    ```
4.  **Run the Main Script:** Use the appropriate command-line arguments as defined in the project (check `main.py` or documentation).
    *   Example for running with display:
        ```bash
        python main.py --camera-ids 0 2 # Use the correct camera IDs
        ```
    *   Example for running headless:
        ```bash
        python main.py --camera-ids 0 2 --headless
        ```

## 6. Troubleshooting & Considerations

*   **Permissions:** You might encounter permission errors accessing USB devices (Coral, Cameras, Zigbee adapter). Ensure your user is part of relevant groups (e.g., `plugdev`, `dialout`, `video`). You might need `udev` rules. The Coral install adds a rule for `/dev/apex_0`, but you might need others.
*   **Performance:** Inference speed, especially CPU fallback, will be slower than on a desktop. Ensure the Coral USB Accelerator is properly detected and used (check application logs). Using a USB 3.0 port is crucial for Coral performance.
*   **Python Version:** Sticking to Python 3.9 is highly recommended due to PyCoral/TFLite Runtime constraints. Using newer Python versions might require unofficial packages, Docker, or building components from source.
*   **OpenCV Installation:** If `pip install opencv-python` fails or causes issues, consult Raspberry Pi specific guides (like those from PyImageSearch or Q-engineering) which might involve different prerequisites or build steps. `opencv-python-headless` is often a more straightforward install if you don't need `cv2.imshow()`.
*   **Dependencies:** If a `pip install` fails for a specific package, check if it needs additional system libraries installed via `apt`.

This guide provides a starting point. You may need to adapt steps based on the specific version of Raspberry Pi OS you use and any changes in dependency requirements. Always refer to the official documentation for Coral, TensorFlow Lite, and OpenCV for the most up-to-date Raspberry Pi instructions.

## 7. Running as a Systemd Service (Auto-start on Boot)

To make the person detection script run automatically when the Raspberry Pi boots up, you can create a systemd service file.

1.  **Create the Service File:**
    Open a new file for the service configuration using a text editor like `nano`:
    ```bash
    sudo nano /etc/systemd/system/smart_office.service
    ```

2.  **Add Service Configuration:**
    Paste the following content into the file. **Make sure to replace placeholders** like `<username>`, `<path_to_project_root>`, and the command-line arguments (`--camera-ids`, `--headless`, etc.) with your actual values.

    ```ini
    [Unit]
    Description=Smart Office Person Detection Service
    # Start after the network is available and the Coral device might be ready
    After=network.target multi-user.target
    # If you have specific services for your cameras or Coral, add them here:
    # Wants=some-camera-service.service

    [Service]
    Type=simple
    # Set the user and group to run the script as (e.g., pi)
    User=<username>
    Group=<groupname>

    # Set the working directory to the 'src' folder
    WorkingDirectory=<path_to_project_root>/python_implementation/src

    # Command to execute: Use absolute path to venv python and main script
    # Ensure you use the correct camera IDs and potentially --headless for boot
    ExecStart=<path_to_project_root>/python_implementation/.venv/bin/python <path_to_project_root>/python_implementation/src/main.py --camera-ids 0 2 --headless

    # Restart the service if it fails
    Restart=on-failure
    RestartSec=5

    # Redirect standard output and error to the systemd journal
    StandardOutput=journal
    StandardError=journal

    [Install]
    # Start the service in the default multi-user runlevel
    WantedBy=multi-user.target
    ```

    **Example Replacements:**
    *   `<username>`: `pi`
    *   `<groupname>`: `pi`
    *   `<path_to_project_root>`: `/home/pi/projects/smart_office_security_v2`
    *   `ExecStart`: `/home/pi/projects/smart_office_security_v2/python_implementation/.venv/bin/python /home/pi/projects/smart_office_security_v2/python_implementation/src/main.py --camera-ids 0 2 --headless` (Adjust camera IDs and headless flag as needed for your auto-start scenario. Using `--headless` is generally recommended for services starting at boot).

3.  **Save and Close:** Press `Ctrl+X`, then `Y`, then `Enter` to save the file in `nano`.

4.  **Reload Systemd Daemon:**
    Tell systemd to scan for new or changed units:
    ```bash
    sudo systemctl daemon-reload
    ```

5.  **Enable the Service:**
    Configure the service to start automatically on boot:
    ```bash
    sudo systemctl enable smart_office.service
    ```

6.  **Start the Service (Optional):**
    You can manually start the service now without rebooting:
    ```bash
    sudo systemctl start smart_office.service
    ```

7.  **Check Service Status:**
    Verify if the service is running correctly:
    ```bash
    sudo systemctl status smart_office.service
    ```
    Look for `active (running)`. Press `q` to exit the status view.

8.  **View Logs:**
    If the service fails or you need to see its output, check the systemd journal:
    ```bash
    journalctl -u smart_office.service
    # To follow logs in real-time:
    # journalctl -f -u smart_office.service
    ```

9.  **Stop/Disable the Service (If needed):**
    ```bash
    # Stop the currently running service
    sudo systemctl stop smart_office.service
    # Prevent the service from starting on boot
    sudo systemctl disable smart_office.service
    ```

Now, the Python application should start automatically the next time you reboot your Raspberry Pi. 