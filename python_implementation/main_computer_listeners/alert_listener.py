# alert_listener.py
import paho.mqtt.client as mqtt
import argparse
import time
import json # Added for parsing structured alerts
from plyer import notification

# For actual desktop notifications, you would typically use a library like 'plyer'.
# Example (requires 'pip install plyer'):
# notification.notify(
#     title='Smart Office Alert',
#     message=alert_message,
#     app_name='Alert Listener',
#     timeout=10  # seconds
# )

MQTT_TOPIC_ALERT = "smart_office/camera/alert"

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[AlertLis] Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC_ALERT)
        print(f"[AlertLis] Subscribed to {MQTT_TOPIC_ALERT}")
    else:
        print(f"[AlertLis] Failed to connect, return code {reason_code}")

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode()
        print(f"\n-------------------------------")
        print(f"[ALERT RAW RECEIVED] {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Topic: {msg.topic}, Payload: {payload_str}")
        
        data = json.loads(payload_str)
        status = data.get("status")
        message = data.get("message", "No message content.") # Default message
        camera_id = data.get("camera_id", "Unknown Camera")

        if status == "PERSON_DETECTED":
            print(f"[ALERT] Status: PERSON_DETECTED, Camera: {camera_id}, Message: {message}")
            try:
                notification.notify(
                    title=f'Smart Office: Person Detected! ({camera_id})',
                    message=message,
                    app_name='Smart Office Alert Listener',
                    timeout=5  # Notification will disappear after 15 seconds
                )
                print("[AlertLis] Desktop notification sent for PERSON_DETECTED.")
            except Exception as e:
                print(f"[AlertLis] Failed to send desktop notification: {e}")
                print("[AlertLis] Ensure 'plyer' is installed and you have a notification server running (e.g., notify-osd).")
        
        elif status == "PERSON_GONE":
            print(f"[STATUS] Status: PERSON_GONE, Camera: {camera_id}, Message: {message}")
            # For now, we don't actively try to dismiss the old notification with plyer.
            # It will disappear based on its own timeout. The main benefit here is stopping repeated PERSON_DETECTED notifications.
            pass # Explicitly do nothing visual for PERSON_GONE for now

        else:
            # Handle messages that are JSON but don't have the expected status
            print(f"[ALERT] Received JSON with unknown status or non-alert message: {payload_str}")
            # Optionally, notify for these as well, or just log
            try:
                notification.notify(
                    title='Smart Office Alert (Unknown Status)',
                    message=payload_str, # Show the full JSON string
                    app_name='Smart Office Alert Listener',
                    timeout=10
                )
                print("[AlertLis] Desktop notification sent for unknown status JSON.")
            except Exception as e:
                print(f"[AlertLis] Failed to send desktop notification for unknown status JSON: {e}")

        print(f"-------------------------------\n")

    except json.JSONDecodeError:
        # Handle cases where the payload is not JSON (e.g., older/simple string alerts)
        alert_message = msg.payload.decode() # Already decoded, but for clarity
        print(f"\n-------------------------------")
        print(f"[ALERT RECEIVED - Non-JSON] {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Message: {alert_message}")
        print(f"-------------------------------\n")
        try:
            notification.notify(
                title='Smart Office Alert!',
                message=alert_message,
                app_name='Smart Office Alert Listener',
                timeout=5  # Notification will disappear after 10 seconds
            )
            print("[AlertLis] Desktop notification sent for non-JSON message.")
        except Exception as e:
            print(f"[AlertLis] Failed to send desktop notification for non-JSON: {e}")
            print("[AlertLis] Ensure 'plyer' is installed and you have a notification server running (e.g., notify-osd).")
    except Exception as e:
        # Catch any other unexpected errors during message processing
        print(f"[AlertLis] Critical error processing message: {e}")
        print(f"Original payload: {msg.payload.decode() if msg else 'N/A'}")

def main(args):
    client = mqtt.Client(client_id=f"alert-listener-{int(time.time())}", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[AlertLis] Connecting to broker at {args.mqtt_broker}:{args.mqtt_port}")
    try:
        client.connect(args.mqtt_broker, args.mqtt_port, 60)
    except Exception as e:
        print(f"[AlertLis] MQTT connection error: {e}")
        # Decide if we should exit or continue if only MQTT fails but serial might work
        # For now, we'll let it proceed if serial is enabled.

    print("[AlertLis] Listening for alerts... Press Ctrl+C to exit.")
    try:
        client.loop_start() # Use loop_start() for non-blocking MQTT loop
        while True:
            time.sleep(1) # Keep main thread alive

    except KeyboardInterrupt:
        print("\n[MainLoop] Interrupted by user. Disconnecting...")
    finally:
        if client.is_connected():
            client.loop_stop()
            client.disconnect()
        print("[AlertLis] Disconnected. Exited.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MQTT Alert Listener")
    parser.add_argument('--mqtt-broker', type=str, default='localhost', help='MQTT broker address')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port')
    args = parser.parse_args()
    main(args) 