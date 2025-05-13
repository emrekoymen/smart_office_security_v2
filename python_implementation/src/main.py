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
            # Frame acquisition with synchronization
            frame_left = None
            frame_right = None
            
            acquisition_start_time = time.time()
            ACQUISITION_TIMEOUT_SECONDS = 2.0 # Wait up to 2 seconds for frames

            while not (cam_left.stopped or cam_right.stopped): # Continue trying if streams are active
                if frame_left is None:
                    frame_left = cam_left.read()
                
                if frame_right is None:
                    frame_right = cam_right.read()

                if frame_left is not None and frame_right is not None:
                    break # Got both frames

                if time.time() - acquisition_start_time > ACQUISITION_TIMEOUT_SECONDS:
                    print("[WARN] Timeout waiting for frames from both cameras during acquisition attempt.")
                    break 
                
                time.sleep(0.01) # Brief pause to yield CPU if waiting

            if cam_left.stopped or cam_right.stopped:
                print("[INFO] A camera stream has stopped. Exiting main processing loop.")
                break

            if frame_left is None or frame_right is None:
                print("[INFO] Skipping processing cycle due to missing frame(s) after acquisition attempt. One or both cameras might be struggling.")
                time.sleep(0.1) # Give a bit more time before retrying
                continue

            current_time = time.time() # Moved here, as it's used after frames are acquired
            # --- Process Left Camera ---
            start_left = time.time()
            detections_left, engine_left = detector.detect(frame_left)
            processed_detections_left = []
            person_detected_left = False
            # disp_frame_left = frame_left.copy() # Base frame for drawing

            for det in detections_left:
                temp_bbox = None
                temp_score = None
                if hasattr(det, 'score') and hasattr(det, 'bbox'): # PyCoral output
                    temp_score = det.score
                    bbox = det.bbox
                    h, w = frame_left.shape[:2]
                    model_input_w, model_input_h = 480.0, 480.0
                    scale_x, scale_y = w / model_input_w, h / model_input_h
                    temp_bbox = [
                        int(bbox.xmin * scale_x), int(bbox.ymin * scale_y),
                        int(bbox.width * scale_x), int(bbox.height * scale_y)
                    ]
                elif isinstance(det, dict) and 'score' in det and 'bbox' in det: # CPU fallback output
                    temp_score = det['score']
                    temp_bbox = det['bbox']

                if temp_score is not None and temp_bbox is not None:
                    processed_detections_left.append({'bbox': temp_bbox, 'score': temp_score})

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
            processed_detections_right = []
            person_detected_right = False
            # disp_frame_right = frame_right.copy() # Base frame for drawing

            for det in detections_right:
                temp_bbox = None
                temp_score = None
                if hasattr(det, 'score') and hasattr(det, 'bbox'): # PyCoral output
                    temp_score = det.score
                    bbox = det.bbox
                    h, w = frame_right.shape[:2]
                    model_input_w, model_input_h = 480.0, 480.0
                    scale_x, scale_y = w / model_input_w, h / model_input_h
                    temp_bbox = [
                        int(bbox.xmin * scale_x), int(bbox.ymin * scale_y),
                        int(bbox.width * scale_x), int(bbox.height * scale_y)
                    ]
                elif isinstance(det, dict) and 'score' in det and 'bbox' in det: # CPU fallback output
                    temp_score = det['score']
                    temp_bbox = det['bbox']

                if temp_score is not None and temp_bbox is not None:
                    processed_detections_right.append({'bbox': temp_bbox, 'score': temp_score})

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
            annotated_frame_left = drawer_left.draw_overlays(frame_left, detections=processed_detections_left, fps=fps_left)
            # Display locally ONLY if not headless
            if not args.headless:
                cv2.imshow(drawer_left.window_name, annotated_frame_left)

            now_right = time.time()
            fps_right = 1.0 / max(now_right - start_right, 1e-6)
            # Get annotated frame from drawer (always needed for stream)
            annotated_frame_right = drawer_right.draw_overlays(frame_right, detections=processed_detections_right, fps=fps_right)
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
    parser.add_argument('--model_tpu', type=str, default='models/output_tflite_graph_edgetpu.tflite')
    parser.add_argument('--model_cpu', type=str, default='models/ssd_mobilenet_v2_coco_quant_postprocess.tflite')
    parser.add_argument('--threshold', type=float, default=0.5)
    parser.add_argument('--headless', action='store_true', help='Run without display windows')
    parser.add_argument('--mqtt-broker', type=str, default='192.168.5.135', help='MQTT broker address')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port')

    args = parser.parse_args()
    main(args)
