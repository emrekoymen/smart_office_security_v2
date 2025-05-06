# alert_listener.py
import paho.mqtt.client as mqtt
import argparse
import time

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

def main(args):
    client = mqtt.Client(client_id=f"alert-listener-{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[AlertLis] Connecting to broker at {args.mqtt_broker}:{args.mqtt_port}")
    try:
        client.connect(args.mqtt_broker, args.mqtt_port, 60)
    except Exception as e:
        print(f"[AlertLis] MQTT connection error: {e}")
        return

    print("[AlertLis] Listening for alerts... Press Ctrl+C to exit.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[AlertLis] Interrupted by user. Disconnecting...")
    finally:
        client.disconnect()
        print("[AlertLis] Disconnected. Exited.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="MQTT Alert Listener")
    parser.add_argument('--mqtt-broker', type=str, default='localhost', help='MQTT broker address')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port')
    args = parser.parse_args()
    main(args) 