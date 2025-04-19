import serial
import json
import time

class ZigbeeSender:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            self.ser = None
            print(f"[Zigbee] Serial init failed: {e}")

    def send_event(self, timestamp, confidence, bbox):
        if self.ser is None:
            print("[Zigbee] Serial not initialized!")
            return
        payload = {
            "timestamp": timestamp,
            "confidence": confidence,
            "bbox": bbox
        }
        try:
            self.ser.write((json.dumps(payload) + '\n').encode())
        except Exception as e:
            print(f"[Zigbee] Send failed: {e}")

    def close(self):
        if self.ser:
            self.ser.close()
