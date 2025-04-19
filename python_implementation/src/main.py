import argparse
import time
from datetime import datetime
import cv2
from camera import CameraStream
from inference import PersonDetector
from display import DisplayWindow
from logger import log_person_detected


def main(args):
    # Camera setup
    cam_left = CameraStream(args.cam0, width=640, height=480, fps=20).start()
    cam_right = CameraStream(args.cam1, width=640, height=480, fps=20).start()
    # Inference engine
    detector = PersonDetector(args.model_tpu, args.model_cpu, threshold=args.threshold)
    # Display
    if not args.headless:
        win_left = DisplayWindow("Camera 0")
        win_right = DisplayWindow("Camera 1")
    prev_time_left = time.time()
    prev_time_right = time.time()
    fps_left = fps_right = 0
    try:
        while True:
            frame_left = cam_left.read()
            frame_right = cam_right.read()
            if frame_left is None or frame_right is None:
                time.sleep(0.01)
                continue
            # LEFT
            start_left = time.time()
            detections_left, engine_left = detector.detect(frame_left)
            bbox_left, score_left = None, None
            # Debug: print detection count and engine
            print(f"[DEBUG] Left: {len(detections_left)} detections, engine={engine_left}")
            for det in detections_left:
                if hasattr(det, 'score'):
                    score_left = det.score
                    bbox = det.bbox
                    # scale bounding box from model input size (300x300) to original frame
                    h, w = frame_left.shape[:2]
                    scale_x = w / 300.0
                    scale_y = h / 300.0
                    bbox_left = [
                        int(bbox.xmin * scale_x),
                        int(bbox.ymin * scale_y),
                        int(bbox.width * scale_x),
                        int(bbox.height * scale_y),
                    ]
                elif 'score' in det:
                    score_left = det['score']
                    bbox_left = det['bbox']
                if score_left is not None:
                    log_person_detected(score_left)
            now_left = time.time()
            fps_left = 1.0 / max(now_left - start_left, 1e-6)
            if not args.headless:
                win_left.show(frame_left, bbox=bbox_left, score=score_left, fps=fps_left)
            # RIGHT
            start_right = time.time()
            detections_right, engine_right = detector.detect(frame_right)
            bbox_right, score_right = None, None
            print(f"[DEBUG] Right: {len(detections_right)} detections, engine={engine_right}")
            for det in detections_right:
                if hasattr(det, 'score'):
                    score_right = det.score
                    bbox = det.bbox
                    # scale bounding box from model input size (300x300) to original frame
                    h, w = frame_right.shape[:2]
                    scale_x = w / 300.0
                    scale_y = h / 300.0
                    bbox_right = [
                        int(bbox.xmin * scale_x),
                        int(bbox.ymin * scale_y),
                        int(bbox.width * scale_x),
                        int(bbox.height * scale_y),
                    ]
                elif 'score' in det:
                    score_right = det['score']
                    bbox_right = det['bbox']
                if score_right is not None:
                    log_person_detected(score_right)
            now_right = time.time()
            fps_right = 1.0 / max(now_right - start_right, 1e-6)
            if not args.headless:
                win_right.show(frame_right, bbox=bbox_right, score=score_right, fps=fps_right)
            # Quit
            if not args.headless and cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cam_left.stop()
        cam_right.stop()
        if not args.headless:
            win_left.close()
            win_right.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cam0', type=int, default=0, help='Camera 0 index')
    parser.add_argument('--cam1', type=int, default=2, help='Camera 1 index')
    parser.add_argument('--model_tpu', type=str, default='models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite')
    parser.add_argument('--model_cpu', type=str, default='models/ssd_mobilenet_v2_coco_quant_postprocess.tflite')
    parser.add_argument('--threshold', type=float, default=0.5)
    parser.add_argument('--headless', action='store_true', help='Run without display windows')
    args = parser.parse_args()
    main(args)
