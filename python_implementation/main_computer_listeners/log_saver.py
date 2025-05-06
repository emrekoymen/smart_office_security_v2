# log_saver.py
import paho.mqtt.client as mqtt
import json
import os
import argparse
from datetime import datetime
import time

MQTT_TOPIC_LOG = "smart_office/camera/detection_log"
LOG_DIR = "detection_logs"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[LogSaver] Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC_LOG)
        print(f"[LogSaver] Subscribed to {MQTT_TOPIC_LOG}")
    else:
        print(f"[LogSaver] Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode()
        # print(f"[LogSaver] Received raw payload: {payload_str[:100]}...") # Debug
        log_data = json.loads(payload_str)
        
        # Try to get a timestamp from the payload, fallback to current time
        timestamp_str = log_data.get("detection_period_end")
        
        if timestamp_str:
            # Try to parse the ISO format timestamp
            try:
                dt_object = datetime.fromisoformat(timestamp_str)
                filename_ts = dt_object.strftime("%Y-%m-%d_%H-%M-%S_%f")
            except ValueError:
                # If parsing fails, use current time as a fallback for filename
                print(f"[LogSaver] Warning: Could not parse timestamp_str '{timestamp_str}'. Using current time for filename.")
                filename_ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        else:
            filename_ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
            
        filename = f"{filename_ts}.json"
        filepath = os.path.join(LOG_DIR, filename)
        
        os.makedirs(LOG_DIR, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=4)
        print(f"[LogSaver] Saved log to {filepath}")
        
    except json.JSONDecodeError as e:
        print(f"[LogSaver] Error decoding JSON: {e}. Payload: {msg.payload.decode()[:200]}...")
    except Exception as e:
        print(f"[LogSaver] Error processing message: {e}")

def main(args):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print(f"[LogSaver] Created log directory: {LOG_DIR}")

    client = mqtt.Client(client_id=f"log-saver-{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[LogSaver] Connecting to broker at {args.mqtt_broker}:{args.mqtt_port}")
    try:
        client.connect(args.mqtt_broker, args.mqtt_port, 60)
    except Exception as e:
        print(f"[LogSaver] MQTT connection error: {e}")
        return

    print(f"[LogSaver] Listening for detection logs... Saving to '{LOG_DIR}' directory. Press Ctrl+C to exit.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[LogSaver] Interrupted by user. Disconnecting...")
    finally:
        client.disconnect()
        print("[LogSaver] Disconnected. Exited.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MQTT Log Saver")
    parser.add_argument('--mqtt-broker', type=str, default='localhost', help='MQTT broker address')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port')
    args = parser.parse_args()
    main(args) 