# Testing & Validation

## 1. Functional Tests
- Person detect on sample videos  
- Fallback behavior

## 2. Performance Benchmarks
- FPS per camera (TPU vs CPU)  
- Latency breakdown

## 3. Edge Cases
- No person  
- Multiple persons  
- TPU disconnect

## 4. Automated Scripts
- CI test commands  
- Sample data

## Python Prototype Tests

- Functional: Person detection on both cameras, fallback by unplugging TPU
- Console output: `Person Detected! (Confidence Score: X)`
- Zigbee: Verify event on receiver
- Headless: `--headless` disables display