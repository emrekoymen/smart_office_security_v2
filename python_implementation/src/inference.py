import numpy as np
import cv2
import time
import os
try:
    from pycoral.utils.edgetpu import make_interpreter
    from pycoral.adapters.common import input_size
    from pycoral.adapters.detect import get_objects
    TPU_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] TPU import failed: {e}")
    TPU_AVAILABLE = False

class PersonDetector:
    def __init__(self, model_path_tpu, model_path_cpu, threshold=0.5, label_path='models/coco_labels.txt'):
        # Resolve model & label paths relative to project root
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        self.model_path_tpu = model_path_tpu if os.path.isabs(model_path_tpu) else os.path.join(base_dir, model_path_tpu)
        self.model_path_cpu = model_path_cpu if os.path.isabs(model_path_cpu) else os.path.join(base_dir, model_path_cpu)
        self.threshold = threshold
        self.label_path = label_path if os.path.isabs(label_path) else os.path.join(base_dir, label_path)
        self.labels = self._load_labels(self.label_path)
        self.tpu_failed = False
        self._init_interpreters()
        if self.interpreter_tpu is None and self.interpreter_cpu is None:
            raise RuntimeError("No valid interpreter (TPU/CPU) available. Check model paths and runtime deps.")

    def _init_interpreters(self):
        self.interpreter_tpu = None
        self.interpreter_cpu = None
        if TPU_AVAILABLE:
            try:
                self.interpreter_tpu = make_interpreter(self.model_path_tpu)
                self.interpreter_tpu.allocate_tensors()
                print("[INFO] TPU interpreter loaded successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to load TPU interpreter: {e}")
                self.tpu_failed = True

        # CPU interpreter init with fallback to tflite_runtime or tensorflow.lite
        Interpreter = None
        try:
            from tflite_runtime.interpreter import Interpreter as TfliteInterpreter
            Interpreter = TfliteInterpreter
            print("[INFO] Using tflite_runtime Interpreter for CPU")
        except ImportError:
            try:
                from tensorflow.lite import Interpreter as TfLiteInterpreter
                Interpreter = TfLiteInterpreter
                print("[INFO] Using tensorflow.lite Interpreter for CPU")
            except ImportError as e:
                print(f"[ERROR] No TFLite runtime found for CPU interpreter: {e}")
        if Interpreter:
            try:
                self.interpreter_cpu = Interpreter(model_path=self.model_path_cpu)
                self.interpreter_cpu.allocate_tensors()
                print("[INFO] CPU interpreter loaded successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to load CPU interpreter: {e}")
                self.interpreter_cpu = None
        else:
            self.interpreter_cpu = None

        # Fatal if neither interpreter is available
        if self.interpreter_tpu is None and self.interpreter_cpu is None:
            print("[FATAL] No valid interpreter available! Check your model files and runtime dependencies.")

    def _load_labels(self, path):
        labels = {}
        try:
            with open(path, 'r') as f:
                for idx, line in enumerate(f):
                    labels[idx] = line.strip()
        except Exception:
            pass
        return labels

    def detect(self, frame):
        # Debug interpreter status
        # print(f"[DEBUG][Inference] TPU_AVAILABLE={TPU_AVAILABLE}, tpu_failed={self.tpu_failed}, tpu_interp_loaded={self.interpreter_tpu is not None}, cpu_interp_loaded={self.interpreter_cpu is not None}")
        
        # Input frame is already grayscale from CameraStream
        # Resize to model input size (e.g., 300x300)
        input_frame_resized = cv2.resize(frame, (300, 300))

        # Ensure input_frame is (H, W, C) - for grayscale, C=1
        if input_frame_resized.ndim == 2:  # Grayscale image (H, W)
            input_frame_reshaped = np.expand_dims(input_frame_resized, axis=-1)  # (H, W, 1)
        elif input_frame_resized.ndim == 3 and input_frame_resized.shape[2] == 1: # Already (H,W,1)
            input_frame_reshaped = input_frame_resized
        else:
            # This case should ideally not be reached if camera provides correct grayscale
            # If it were BGR, we would convert: cv2.cvtColor(input_frame_resized, cv2.COLOR_BGR2GRAY)
            # and then expand_dims. But since we expect grayscale, this is an error/unexpected state.
            print(f"[ERROR][Inference] Unexpected frame dimensions: {input_frame_resized.shape}. Expected grayscale.")
            # Fallback: try to take the first channel if it's 3-channel, or error out
            if input_frame_resized.ndim == 3 and input_frame_resized.shape[2] == 3:
                 print("[WARN][Inference] Taking first channel of 3-channel image as grayscale.")
                 input_frame_reshaped = np.expand_dims(input_frame_resized[:,:,0], axis=-1)
            else:
                return [], 'NONE' # Cannot process

        # Add batch dimension: (1, H, W, 1)
        input_data = np.expand_dims(input_frame_reshaped, axis=0)
        input_data = input_data.astype(np.uint8)

        # Try TPU first
        if TPU_AVAILABLE and not self.tpu_failed and self.interpreter_tpu:
            try:
                self.interpreter_tpu.set_tensor(self.interpreter_tpu.get_input_details()[0]['index'], input_data)
                self.interpreter_tpu.invoke()
                objs = get_objects(self.interpreter_tpu, self.threshold)
                # Filter for person class only (index 0)
                filtered = [o for o in objs if hasattr(o, 'id') and o.id == 0]
                return filtered, 'TPU'
            except Exception:
                self.tpu_failed = True
        # Fallback to CPU
        if self.interpreter_cpu:
            self.interpreter_cpu.set_tensor(self.interpreter_cpu.get_input_details()[0]['index'], input_data)
            self.interpreter_cpu.invoke()
            output_details = self.interpreter_cpu.get_output_details()
            boxes = self.interpreter_cpu.get_tensor(output_details[0]['index'])[0]  # Bounding box coordinates
            classes = self.interpreter_cpu.get_tensor(output_details[1]['index'])[0]  # Class index
            scores = self.interpreter_cpu.get_tensor(output_details[2]['index'])[0]  # Confidence
            detections = []
            # Original frame dimensions (from the input grayscale frame)
            orig_h, orig_w = frame.shape[:2] 

            for i in range(len(scores)):
                if int(classes[i]) == 0 and scores[i] > self.threshold:
                    ymin, xmin, ymax, xmax = boxes[i]
                    # Bounding box coordinates are relative to the input size of the model (300x300)
                    # Scale them to the original frame dimensions
                    detections.append({
                        'bbox': [
                            int(xmin * orig_w), 
                            int(ymin * orig_h), 
                            int((xmax - xmin) * orig_w), 
                            int((ymax - ymin) * orig_h)
                        ],
                        'score': float(scores[i])
                    })
            return detections, 'CPU'
        return [], 'NONE'
