# alert_listener.py
import paho.mqtt.client as mqtt
import argparse
import time
import serial # Added for serial communication
import threading # Added for concurrent serial reading

# For actual desktop notifications, you would typically use a library like 'plyer'.
# Example (requires 'pip install plyer'):
# from plyer import notification
# notification.notify(
#     title='Smart Office Alert',
#     message=alert_message,
#     app_name='Alert Listener',
#     timeout=10  # seconds
# )

MQTT_TOPIC_ALERT = "smart_office/camera/alert"
SERIAL_DATA_BUFFER = [] # Buffer to store incoming serial data (optional, for more complex processing)
SERIAL_THREAD_STOP_EVENT = threading.Event() # Event to signal the serial thread to stop

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[AlertLis] Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC_ALERT)
        print(f"[AlertLis] Subscribed to {MQTT_TOPIC_ALERT}")
    else:
        print(f"[AlertLis] Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    alert_message = msg.payload.decode()
    print(f"\n-------------------------------")
    print(f"[ALERT RECEIVED] {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Message: {alert_message}")
    print(f"-------------------------------\n")
    # To trigger a desktop notification, you would call a function here.
    # e.g., using plyer as shown in the comments at the top of the file.
    # For now, it just prints to console.

def read_from_serial_port(serial_port, baud_rate):
    """Reads data from the specified serial port and prints it."""
    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        print(f"[SerialLis] Connected to serial port {serial_port} at {baud_rate} baud.")
        print(f"[SerialLis] Listening for data... Press Ctrl+C in main terminal to exit.")
        while not SERIAL_THREAD_STOP_EVENT.is_set():
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8', errors='replace').rstrip()
                    if line:
                        print(f"\n-------------------------------")
                        print(f"[SERIAL DATA RECEIVED] {time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"Port: {serial_port}, Data: {line}")
                        print(f"-------------------------------\n")
                        # Optionally, add to buffer for other processing:
                        # SERIAL_DATA_BUFFER.append(line)
                except serial.SerialException as e:
                    print(f"[SerialLis] Error reading from serial port {serial_port}: {e}")
                    break # Exit thread on serial error
                except UnicodeDecodeError as e:
                    print(f"[SerialLis] Error decoding serial data: {e}. Raw: {ser.readline()}")
            time.sleep(0.1) # Small delay to prevent busy-waiting
    except serial.SerialException as e:
        print(f"[SerialLis] Could not open serial port {serial_port}: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
        print(f"[SerialLis] Serial port {serial_port} closed.")

def main(args):
    client = mqtt.Client(client_id=f"alert-listener-{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[AlertLis] Connecting to broker at {args.mqtt_broker}:{args.mqtt_port}")
    try:
        client.connect(args.mqtt_broker, args.mqtt_port, 60)
    except Exception as e:
        print(f"[AlertLis] MQTT connection error: {e}")
        # Decide if we should exit or continue if only MQTT fails but serial might work
        # For now, we'll let it proceed if serial is enabled.

    # Start the serial listener thread if a port is specified
    serial_thread = None
    if args.serial_port:
        serial_thread = threading.Thread(target=read_from_serial_port, args=(args.serial_port, args.serial_baud_rate), daemon=True)
        serial_thread.start()
    else:
        print("[SerialLis] No serial port specified. Skipping serial data listening.")

    print("[AlertLis] Listening for alerts... Press Ctrl+C to exit.")
    try:
        client.loop_start() # Use loop_start() for non-blocking MQTT loop
        while True:
            time.sleep(1) # Keep main thread alive
            # Here you could add logic to check SERIAL_DATA_BUFFER if needed
            if serial_thread and not serial_thread.is_alive() and args.serial_port:
                print("[MainLoop] Serial thread seems to have terminated unexpectedly.")
                # Optionally, try to restart it or handle the error.
                break # Exit main loop if serial thread dies

    except KeyboardInterrupt:
        print("\n[MainLoop] Interrupted by user. Disconnecting...")
    finally:
        SERIAL_THREAD_STOP_EVENT.set() # Signal serial thread to stop
        if serial_thread and serial_thread.is_alive():
            print("[MainLoop] Waiting for serial thread to finish...")
            serial_thread.join(timeout=5) # Wait for the serial thread to exit
            if serial_thread.is_alive():
                print("[MainLoop] Serial thread did not stop in time.")
        
        if client.is_connected():
            client.loop_stop()
            client.disconnect()
        print("[AlertLis] Disconnected. Exited.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MQTT Alert Listener with USB Serial Data Logging")
    parser.add_argument('--mqtt-broker', type=str, default='localhost', help='MQTT broker address')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--serial-port', type=str, default='/dev/ttyUSB0', help='Serial port for USB device (e.g., /dev/ttyUSB0 or COM3)')
    parser.add_argument('--serial-baud-rate', type=int, default=9600, help='Baud rate for the serial port')
    args = parser.parse_args()
    main(args) 