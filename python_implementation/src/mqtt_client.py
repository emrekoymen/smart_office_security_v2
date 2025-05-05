import paho.mqtt.client as mqtt
import time
import json

class MQTTClient:
    def __init__(self, broker_address, port=1883, client_id=""):
        self.broker_address = broker_address
        self.port = port
        # Use a default client_id or generate a unique one if needed
        self.client_id = client_id if client_id else f"python-mqtt-{int(time.time())}"
        self.client = mqtt.Client(client_id=self.client_id)
        self.is_connected = False

        # Assign callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] Connected successfully to broker at {self.broker_address}")
            self.is_connected = True
        else:
            print(f"[MQTT] Connection failed with code {rc}")
            self.is_connected = False

    def _on_disconnect(self, client, userdata, rc):
        print(f"[MQTT] Disconnected with result code {rc}")
        self.is_connected = False
        # Optional: Implement automatic reconnection logic here if needed

    def connect(self):
        try:
            print(f"[MQTT] Attempting to connect to {self.broker_address}:{self.port}...")
            self.client.connect(self.broker_address, self.port, 60)
            self.client.loop_start() # Start background thread for network traffic
        except Exception as e:
            print(f"[MQTT] Connection error: {e}")
            self.is_connected = False

    def disconnect(self):
        if self.is_connected:
            print("[MQTT] Disconnecting...")
            self.client.loop_stop() # Stop the background thread
            self.client.disconnect()
        else:
             print("[MQTT] Already disconnected or connection never established.")


    def publish(self, topic, payload, qos=1):
        if not self.is_connected:
            print("[MQTT] Cannot publish, not connected.")
            return False
        try:
            # If payload is dict, dump as JSON string
            if isinstance(payload, dict):
                payload_str = json.dumps(payload)
            elif isinstance(payload, bytes):
                 payload_str = payload # Assume bytes payload (like image data) is already formatted
            else:
                 payload_str = str(payload) # Convert other types to string

            result = self.client.publish(topic, payload_str, qos=qos)
            # result.wait_for_publish() # Optional: block until published if needed
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                # print(f"[MQTT] Published to {topic}") # Verbose logging
                return True
            else:
                print(f"[MQTT] Failed to publish to {topic}, error code: {result.rc}")
                return False
        except Exception as e:
            print(f"[MQTT] Error during publish to {topic}: {e}")
            return False 