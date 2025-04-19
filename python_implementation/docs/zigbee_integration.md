# Zigbee Integration

## 1. Hardware & Interface
- XBee / other module  
- Serial settings (baud, port)

## 2. Payload Schema
```json
{
  "timestamp": "ISO8601",
  "confidence": 0.85,
  "bbox": [x, y, w, h]
}
```

## Python Implementation

- Serial transmission implemented in `src/zigbee.py`
- Payload: `{ "timestamp": <ISO8601>, "confidence": <float>, "bbox": [x, y, w, h] }`
- Uses `pyserial` for event sending
- CLI flag for serial port selection