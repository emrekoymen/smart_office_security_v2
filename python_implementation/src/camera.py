import cv2
import threading
import time

class CameraStream:
    def __init__(self, src, width=640, height=480, fps=20):
        self.src = src
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.frame = None
        self.stopped = False
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.update, daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                # Attempt to re-open the camera if reading fails
                print(f"[Camera {self.src}] Frame read failed. Attempting to reopen...")
                self.cap.release()
                time.sleep(0.5) # Brief pause before retrying
                self.cap = cv2.VideoCapture(self.src)
                if not self.cap.isOpened():
                    print(f"[Camera {self.src}] Failed to reopen camera. Stopping thread.")
                    self.stopped = True # Stop if cannot reopen
                    continue
                else:
                    print(f"[Camera {self.src}] Reopened camera successfully.")
                    # Re-apply settings if necessary, though VideoCapture usually retains them if reopened quickly
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                    continue # Retry reading
            
            # Convert frame to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            with self.lock:
                self.frame = gray_frame.copy()
            time.sleep(1 / self.fps) # Adhere to specified FPS

    def read(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.stopped = True
        self.cap.release()
