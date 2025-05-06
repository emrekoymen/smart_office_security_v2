# mqtt_video_viewer.py
import cv2
import paho.mqtt.client as mqtt
import numpy as np
import argparse
import time

MQTT_TOPIC_STREAM_0 = "smart_office/camera/0/stream"
MQTT_TOPIC_STREAM_1 = "smart_office/camera/1/stream"

# Global dictionary to store the latest frame for each camera
latest_frames = {MQTT_TOPIC_STREAM_0: None, MQTT_TOPIC_STREAM_1: None}
last_message_time = {MQTT_TOPIC_STREAM_0: 0, MQTT_TOPIC_STREAM_1: 0}

WINDOW_CAM_0 = "Camera 0 Stream"
WINDOW_CAM_1 = "Camera 1 Stream"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[Viewer] Connected to MQTT Broker!")
        client.subscribe([(MQTT_TOPIC_STREAM_0, 0), (MQTT_TOPIC_STREAM_1, 0)])
        print(f"[Viewer] Subscribed to {MQTT_TOPIC_STREAM_0} and {MQTT_TOPIC_STREAM_1}")
    else:
        print(f"[Viewer] Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global latest_frames, last_message_time
    try:
        nparr = np.frombuffer(msg.payload, np.uint8)
        # Decode the JPEG image bytes as color
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is not None:
            latest_frames[msg.topic] = frame
            last_message_time[msg.topic] = time.time()
        # else:
            # print(f"[Viewer] Failed to decode frame from topic {msg.topic}")
    except Exception as e:
        print(f"[Viewer] Error processing message on {msg.topic}: {e}")

def main(args):
    client = mqtt.Client(client_id=f"viewer-{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[Viewer] Connecting to broker at {args.mqtt_broker}:{args.mqtt_port}")
    try:
        client.connect(args.mqtt_broker, args.mqtt_port, 60)
    except Exception as e:
        print(f"[Viewer] MQTT connection error: {e}")
        return

    client.loop_start()

    cv2.namedWindow(WINDOW_CAM_0, cv2.WINDOW_NORMAL)
    cv2.namedWindow(WINDOW_CAM_1, cv2.WINDOW_NORMAL)

    try:
        while True:
            frame0 = latest_frames[MQTT_TOPIC_STREAM_0]
            frame1 = latest_frames[MQTT_TOPIC_STREAM_1]

            if frame0 is not None:
                cv2.imshow(WINDOW_CAM_0, frame0)
            else:
                # Optional: Display a placeholder if no frame received yet or timeout
                # Ensure placeholder is 3-channel BGR
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8) 
                cv2.putText(placeholder, "Waiting for Cam 0...", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow(WINDOW_CAM_0, placeholder)

            if frame1 is not None:
                cv2.imshow(WINDOW_CAM_1, frame1)
            else:
                # Ensure placeholder is 3-channel BGR
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Waiting for Cam 1...", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow(WINDOW_CAM_1, placeholder)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[Viewer] 'q' pressed, exiting...")
                break
            
            # Check for stale frames (optional)
            # current_ts = time.time()
            # if current_ts - last_message_time[MQTT_TOPIC_STREAM_0] > 5: # 5 second timeout
            #     latest_frames[MQTT_TOPIC_STREAM_0] = None # Clear stale frame
            # if current_ts - last_message_time[MQTT_TOPIC_STREAM_1] > 5:
            #     latest_frames[MQTT_TOPIC_STREAM_1] = None

            time.sleep(0.03) # Approx 30 FPS display loop

    except KeyboardInterrupt:
        print("[Viewer] Interrupted by user (Ctrl+C)")
    finally:
        print("[Viewer] Cleaning up...")
        client.loop_stop()
        client.disconnect()
        cv2.destroyAllWindows()
        print("[Viewer] Exited.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MQTT Video Stream Viewer")
    parser.add_argument('--mqtt-broker', type=str, default='localhost', help='MQTT broker address')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port')
    args = parser.parse_args()
    main(args) 