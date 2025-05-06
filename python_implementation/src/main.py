import argparse
import time
from datetime import datetime
import cv2
import json # Added for MQTT JSON payload
from camera import CameraStream
from inference import PersonDetector
from display import DisplayWindow
from logger import log_person_detected # Keep for local logging if desired
from mqtt_client import MQTTClient # Added


# MQTT Topics
TOPIC_ALERT = "smart_office/camera/alert"
TOPIC_LOG = "smart_office/camera/detection_log"
TOPIC_STREAM_0 = "smart_office/camera/0/stream"
TOPIC_STREAM_1 = "smart_office/camera/1/stream"


def main(args):
    # --- MQTT Setup ---
    mqtt_client = MQTTClient(args.mqtt_broker, args.mqtt_port)
    mqtt_client.connect()
    # Give a moment for the connection to establish
    time.sleep(1)
    if not mqtt_client.is_connected:
        print("[ERROR] Failed to connect to MQTT broker. Exiting.")
        # Optionally handle differently, e.g., run without MQTT?
        return

    # Camera setup
    cam_left = CameraStream(args.cam0, width=640, height=480, fps=20).start()
    cam_right = CameraStream(args.cam1, width=640, height=480, fps=20).start()
    # Inference engine
    detector = PersonDetector(args.model_tpu, args.model_cpu, threshold=args.threshold)

    # Display / Drawing Setup
    # We need the drawing object even if headless, for stream annotations
    drawer_left = DisplayWindow("Camera 0")
    drawer_right = DisplayWindow("Camera 1")
    if not args.headless:
        drawer_left.create_window() # Create windows only if not headless
        drawer_right.create_window()

    # --- State for detection logging ---
    detection_buffer_cam0 = []
    detection_buffer_cam1 = []
    last_detection_time = 0.0 # Timestamp of the last detection event on *any* camera

    try:
        while True:
            current_time = time.time()
            frame_left = cam_left.read()
            frame_right = cam_right.read()
            if frame_left is None or frame_right is None:
                time.sleep(0.01)
                continue

            # --- Process Left Camera ---
            start_left = time.time()
            detections_left, engine_left = detector.detect(frame_left)
            bbox_left, score_left = None, None
            person_detected_left = False
            # disp_frame_left = frame_left.copy() # Base frame for drawing

            for det in detections_left:
                temp_bbox = None
                temp_score = None
                if hasattr(det, 'score') and hasattr(det, 'bbox'): # PyCoral output
                    temp_score = det.score
                    bbox = det.bbox
                    h, w = frame_left.shape[:2]
                    scale_x, scale_y = w / 300.0, h / 300.0
                    temp_bbox = [
                        int(bbox.xmin * scale_x), int(bbox.ymin * scale_y),
                        int(bbox.width * scale_x), int(bbox.height * scale_y)
                    ]
                elif isinstance(det, dict) and 'score' in det and 'bbox' in det: # CPU fallback output
                    temp_score = det['score']
                    temp_bbox = det['bbox']

                if temp_score is not None and temp_bbox is not None:
                    if score_left is None: # Take the first one for display/drawing
                         score_left = temp_score
                         bbox_left = temp_bbox

                    detection_data = {
                        "timestamp": datetime.now().isoformat(),
                        "confidence": float(temp_score),
                        "bbox": temp_bbox
                    }
                    detection_buffer_cam0.append(detection_data)
                    person_detected_left = True

            if person_detected_left:
                 last_detection_time = current_time
                 alert_msg = f"Unauthorized Entrance! Person Detected from Camera 0"
                 mqtt_client.publish(TOPIC_ALERT, alert_msg, qos=1)


            # --- Process Right Camera ---
            start_right = time.time()
            detections_right, engine_right = detector.detect(frame_right)
            bbox_right, score_right = None, None
            person_detected_right = False
            # disp_frame_right = frame_right.copy() # Base frame for drawing

            for det in detections_right:
                temp_bbox = None
                temp_score = None
                if hasattr(det, 'score') and hasattr(det, 'bbox'): # PyCoral output
                    temp_score = det.score
                    bbox = det.bbox
                    h, w = frame_right.shape[:2]
                    scale_x, scale_y = w / 300.0, h / 300.0
                    temp_bbox = [
                        int(bbox.xmin * scale_x), int(bbox.ymin * scale_y),
                        int(bbox.width * scale_x), int(bbox.height * scale_y)
                    ]
                elif isinstance(det, dict) and 'score' in det and 'bbox' in det: # CPU fallback output
                    temp_score = det['score']
                    temp_bbox = det['bbox']

                if temp_score is not None and temp_bbox is not None:
                    if score_right is None: # Take the first one for display/drawing
                         score_right = temp_score
                         bbox_right = temp_bbox

                    detection_data = {
                        "timestamp": datetime.now().isoformat(),
                        "confidence": float(temp_score),
                        "bbox": temp_bbox
                    }
                    detection_buffer_cam1.append(detection_data)
                    person_detected_right = True

            if person_detected_right:
                 last_detection_time = current_time
                 alert_msg = f"Unauthorized Entrance! Person Detected from Camera 1"
                 mqtt_client.publish(TOPIC_ALERT, alert_msg, qos=1)


            # --- Check for logging buffer timeout ---
            if last_detection_time > 0 and (current_time - last_detection_time) > 5.0:
                if detection_buffer_cam0 or detection_buffer_cam1:
                    print(f"[MQTT] Sending detection log ({(current_time - last_detection_time):.1f}s since last detection)")
                    log_payload = {
                        "detection_period_end": datetime.now().isoformat(),
                        "camera_0_detections": detection_buffer_cam0,
                        "camera_1_detections": detection_buffer_cam1
                    }
                    mqtt_client.publish(TOPIC_LOG, log_payload, qos=1)
                    detection_buffer_cam0 = []
                    detection_buffer_cam1 = []
                last_detection_time = 0.0

            # --- Calculate FPS, Draw Overlays, and Display/Stream ---
            now_left = time.time()
            fps_left = 1.0 / max(now_left - start_left, 1e-6)
            # Get annotated frame from drawer (always needed for stream)
            annotated_frame_left = drawer_left.draw_overlays(frame_left, bbox=bbox_left, score=score_left, fps=fps_left)
            # Display locally ONLY if not headless
            if not args.headless:
                cv2.imshow(drawer_left.window_name, annotated_frame_left)

            now_right = time.time()
            fps_right = 1.0 / max(now_right - start_right, 1e-6)
            # Get annotated frame from drawer (always needed for stream)
            annotated_frame_right = drawer_right.draw_overlays(frame_right, bbox=bbox_right, score=score_right, fps=fps_right)
            # Display locally ONLY if not headless
            if not args.headless:
                 cv2.imshow(drawer_right.window_name, annotated_frame_right)

            # --- Stream Frames ---
            jpeg_quality = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
            ret_l, buffer_l = cv2.imencode('.jpg', annotated_frame_left, jpeg_quality)
            ret_r, buffer_r = cv2.imencode('.jpg', annotated_frame_right, jpeg_quality)

            if ret_l:
                mqtt_client.publish(TOPIC_STREAM_0, buffer_l.tobytes(), qos=0)
            if ret_r:
                mqtt_client.publish(TOPIC_STREAM_1, buffer_r.tobytes(), qos=0)

            # Quit condition
            if not args.headless and cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        print("Cleaning up...")
        cam_left.stop()
        cam_right.stop()
        if not args.headless:
             # drawer_left/right are DisplayWindow instances
             drawer_left.close()
             drawer_right.close()
        cv2.destroyAllWindows() # Close any OpenCV windows
        mqtt_client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cam0', type=int, default=0, help='Camera 0 index')
    parser.add_argument('--cam1', type=int, default=2, help='Camera 1 index')
    parser.add_argument('--model_tpu', type=str, default='output_tflite_graph_edgetpu.tflite')
    parser.add_argument('--model_cpu', type=str, default='models/ssd_mobilenet_v2_coco_quant_postprocess.tflite')
    parser.add_argument('--threshold', type=float, default=0.5)
    parser.add_argument('--headless', action='store_true', help='Run without display windows')
    parser.add_argument('--mqtt-broker', type=str, default='192.168.5.135', help='MQTT broker address')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port')

    args = parser.parse_args()
    main(args)
