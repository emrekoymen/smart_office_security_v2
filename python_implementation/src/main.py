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

# Target processing FPS for the main loop
TARGET_PROCESSING_FPS = 20.0
TARGET_LOOP_INTERVAL = 1.0 / TARGET_PROCESSING_FPS


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
    if cam_left and not cam_left.stopped:
        print(f"[INFO] Camera 0 (source: {args.cam0}) initialized and stream active.")
    else:
        print(f"[ERROR] Camera 0 (source: {args.cam0}) failed to start or stream is not active.")

    cam_right = CameraStream(args.cam1, width=640, height=480, fps=20).start()
    if cam_right and not cam_right.stopped:
        print(f"[INFO] Camera 1 (source: {args.cam1}) initialized and stream active.")
    else:
        print(f"[ERROR] Camera 1 (source: {args.cam1}) failed to start or stream is not active.")

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
    left_detection_fps = 0.0 # Initialize FPS for left camera detection display
    right_detection_fps = 0.0 # Initialize FPS for right camera detection display

    # --- State for granular person presence alerts ---
    person_continuously_present_cam0 = False
    last_person_seen_time_cam0 = 0.0
    person_continuously_present_cam1 = False
    last_person_seen_time_cam1 = 0.0
    NO_PERSON_GRACE_PERIOD = 2.5  # Seconds before declaring a person "gone"

    try:
        while True:
            loop_start_time = time.time() # Record start time of the loop iteration

            # Frame acquisition
            frame_left = None
            if not cam_left.stopped:
                frame_left = cam_left.read()
                # Optional: if frame_left is None and not cam_left.stopped:
                #     print(f"[WARN] Left camera ({args.cam0}) active but no frame received this cycle (read returned None).")

            frame_right = None
            if not cam_right.stopped:
                frame_right = cam_right.read()
                # Optional: if frame_right is None and not cam_right.stopped:
                #     print(f"[WARN] Right camera ({args.cam1}) active but no frame received this cycle (read returned None).")
            
            # Exit main loop only if BOTH cameras are stopped
            # REMOVED: This condition is removed to allow cameras to attempt reconnection.
            # if cam_left.stopped and cam_right.stopped:
            #     print("[INFO] Both camera streams appear to be stopped. Exiting main processing loop.")
            #     break

            current_time = time.time()
            jpeg_quality = [int(cv2.IMWRITE_JPEG_QUALITY), 75] # Define once

            # --- Process Left Camera ---
            if frame_left is not None:
                detection_start_time = time.time()
                detections_left, engine_left = detector.detect(frame_left)
                detection_time_left = time.time() - detection_start_time
                if detection_time_left > 0:
                    left_detection_fps = 1.0 / detection_time_left
                else:
                    left_detection_fps = 0 # Avoid division by zero
                
                processed_detections_left = []
                person_detected_left = False

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
                     last_person_seen_time_cam0 = current_time # Update when person is seen
                     if not person_continuously_present_cam0:
                         person_continuously_present_cam0 = True
                         alert_payload = {
                             "status": "PERSON_DETECTED",
                             "camera_id": "Camera 0",
                             "message": f"Unauthorized Entrance! Person Detected from Camera 0 at {datetime.now().strftime('%H:%M:%S')}"
                         }
                         mqtt_client.publish(TOPIC_ALERT, alert_payload, qos=1)
                         print("[MQTT] Sent PERSON_DETECTED alert for Camera 0")
                     last_detection_time = current_time # Global log timer
                # else: # This 'else' would be if person_detected_left is false for the current frame
                    # The 'gone' logic is handled later based on timeout

                # Calculate FPS, Draw Overlays
                annotated_frame_left = drawer_left.draw_overlays(frame_left, detections=processed_detections_left, fps=left_detection_fps)
                
                if not args.headless:
                    cv2.imshow(drawer_left.window_name, annotated_frame_left)

                # Stream Left Frame
                ret_l, buffer_l = cv2.imencode('.jpg', annotated_frame_left, jpeg_quality)
                if ret_l:
                    mqtt_client.publish(TOPIC_STREAM_0, buffer_l.tobytes(), qos=0)
                else:
                    if not cam_left.stopped: # Camera is supposed to be active but gave no frame
                        print("[WARN] Left camera: No frame to process this cycle, but stream is reported active.")
                    # If cam_left.stopped is True, we just skip, no message needed as it's expected.
                    else:
                        print("[WARN] Failed to encode left frame for MQTT.")
            else:
                if cam_left.stopped:
                    print(f"[INFO] Left camera ({args.cam0}) is currently disconnected. Waiting for reconnection...")
                elif not cam_left.stopped and frame_left is None: # Should ideally not happen if read() is robust, but good for debug
                    print(f"[INFO] Left camera ({args.cam0}) is active but no frame was processed/available this cycle.")
                # No message if cam_left.stopped is False and frame_left was processed, or if it was stopped and we expect no frame.

            # --- Process Right Camera ---
            if frame_right is not None:
                detection_start_time_right = time.time()
                detections_right, engine_right = detector.detect(frame_right)
                detection_time_right = time.time() - detection_start_time_right
                if detection_time_right > 0:
                    right_detection_fps = 1.0 / detection_time_right
                else:
                    right_detection_fps = 0 # Avoid division by zero

                processed_detections_right = []
                person_detected_right = False

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
                     last_person_seen_time_cam1 = current_time # Update when person is seen
                     if not person_continuously_present_cam1:
                         person_continuously_present_cam1 = True
                         alert_payload = {
                             "status": "PERSON_DETECTED",
                             "camera_id": "Camera 1",
                             "message": f"Unauthorized Entrance! Person Detected from Camera 1 at {datetime.now().strftime('%H:%M:%S')}"
                         }
                         mqtt_client.publish(TOPIC_ALERT, alert_payload, qos=1)
                         print("[MQTT] Sent PERSON_DETECTED alert for Camera 1")
                     last_detection_time = current_time # Global log timer
                # else: # This 'else' for person_detected_right is false
                    # The 'gone' logic is handled later

                # Calculate FPS, Draw Overlays
                annotated_frame_right = drawer_right.draw_overlays(frame_right, detections=processed_detections_right, fps=right_detection_fps)

                if not args.headless:
                     cv2.imshow(drawer_right.window_name, annotated_frame_right)

                # Stream Right Frame
                ret_r, buffer_r = cv2.imencode('.jpg', annotated_frame_right, jpeg_quality)
                if ret_r:
                    mqtt_client.publish(TOPIC_STREAM_1, buffer_r.tobytes(), qos=0)
                else:
                    if not cam_right.stopped: # Camera is supposed to be active but gave no frame
                        print("[WARN] Right camera: No frame to process this cycle, but stream is reported active.")
                    # If cam_right.stopped is True, we just skip.
                    else:
                        print("[WARN] Failed to encode right frame for MQTT.")
            else:
                if cam_right.stopped:
                    print(f"[INFO] Right camera ({args.cam1}) is currently disconnected. Waiting for reconnection...")
                elif not cam_right.stopped and frame_right is None: # Debug / transient state
                    print(f"[INFO] Right camera ({args.cam1}) is active but no frame was processed/available this cycle.")

            # --- Check for person disappearance (after processing both cameras) ---
            # Use a consistent current time for these checks
            current_time_for_disappearance_check = time.time()

            if (person_continuously_present_cam0 and
               (current_time_for_disappearance_check - last_person_seen_time_cam0 > NO_PERSON_GRACE_PERIOD)):
                # This implies person_detected_left has been false for NO_PERSON_GRACE_PERIOD
                person_continuously_present_cam0 = False
                status_payload = {
                    "status": "PERSON_GONE",
                    "camera_id": "Camera 0",
                    "message": f"Person no longer detected at Camera 0 ({datetime.now().strftime('%H:%M:%S')})"
                }
                mqtt_client.publish(TOPIC_ALERT, status_payload, qos=1) # Send to same alert topic
                print(f"[MQTT] Sent PERSON_GONE for Cam0. Grace: {current_time_for_disappearance_check - last_person_seen_time_cam0:.1f}s.")

            if (person_continuously_present_cam1 and
               (current_time_for_disappearance_check - last_person_seen_time_cam1 > NO_PERSON_GRACE_PERIOD)):
                # This implies person_detected_right has been false for NO_PERSON_GRACE_PERIOD
                person_continuously_present_cam1 = False
                status_payload = {
                    "status": "PERSON_GONE",
                    "camera_id": "Camera 1",
                    "message": f"Person no longer detected at Camera 1 ({datetime.now().strftime('%H:%M:%S')})"
                }
                mqtt_client.publish(TOPIC_ALERT, status_payload, qos=1) # Send to same alert topic
                print(f"[MQTT] Sent PERSON_GONE for Cam1. Grace: {current_time_for_disappearance_check - last_person_seen_time_cam1:.1f}s.")

            # --- Check for logging buffer timeout ---
            if last_detection_time > 0 and (current_time - last_detection_time) > 5.0: # Check global log timer
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

            # Quit condition
            if not args.headless and cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # --- Throttle the main loop to target processing FPS ---
            loop_elapsed_time = time.time() - loop_start_time
            
            sleep_duration = TARGET_LOOP_INTERVAL - loop_elapsed_time
            if sleep_duration > 0:
                time.sleep(sleep_duration)

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
    parser.add_argument('--threshold', type=float, default=0.7)
    parser.add_argument('--headless', action='store_true', help='Run without display windows')
    parser.add_argument('--mqtt-broker', type=str, default='192.168.5.135', help='MQTT broker address')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT broker port')

    args = parser.parse_args()
    main(args)
