import cv2
import threading
import time

class CameraStream:
    def __init__(self, src, width=640, height=480, fps=20):
        self.src = src
        self.width = width
        self.height = height
        self.fps = fps if fps > 0 else 1 # Avoid division by zero later, ensure a minimal delay
        self.cap = cv2.VideoCapture(self.src)
        self.frame = None
        self.lock = threading.Lock()
        self.user_requested_stop = False # True if stop() has been called by the user
        
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps if self.fps > 0 else 30) # Pass a valid FPS to OpenCV
            self.stopped = False # Indicates current operational status
            print(f"[Camera {self.src}] Initialized and opened successfully.")
        else:
            self.stopped = True # Not operational initially
            print(f"[Camera {self.src}] Failed to open on initialization. Will attempt to connect.")

    def start(self):
        # Ensure only one update thread runs
        if hasattr(self, '_update_thread') and self._update_thread.is_alive():
            print(f"[Camera {self.src}] Update thread already running.")
            return self
        self._update_thread = threading.Thread(target=self.update, daemon=True)
        self._update_thread.start()
        print(f"[Camera {self.src}] Update thread started.")
        return self

    def update(self):
        connection_retry_interval_seconds = 2.0
        last_connection_attempt_time = 0

        while not self.user_requested_stop:
            if not self.cap.isOpened():
                current_time = time.time()
                if current_time - last_connection_attempt_time > connection_retry_interval_seconds:
                    print(f"[Camera {self.src}] Attempting to connect...")
                    self.cap.open(self.src) # Try to open/reopen
                    last_connection_attempt_time = current_time

                    if self.cap.isOpened():
                        print(f"[Camera {self.src}] Reconnected successfully.")
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                        self.cap.set(cv2.CAP_PROP_FPS, self.fps if self.fps > 0 else 30)
                        self.stopped = False # Now operational
                    else:
                        # print(f"[Camera {self.src}] Connection attempt failed. Retrying later.")
                        self.stopped = True # Still not operational
                
                if not self.cap.isOpened(): # If still not open after attempt, sleep before next cycle
                    time.sleep(0.5) # Shorter sleep to be responsive to user_requested_stop
                    continue

            # If we are here, cap should be open or just became open.
            if not self.cap.isOpened(): # Should not be strictly necessary but as a safeguard
                self.stopped = True
                time.sleep(0.1) # Brief pause
                continue

            ret, frame_read = self.cap.read()

            if not ret:
                if not self.user_requested_stop: # Avoid error message if we are stopping
                    print(f"[Camera {self.src}] Frame read failed. Attempting to reopen.")
                self.stopped = True # Mark as not operational
                self.cap.release() # Release it so the next loop iteration tries to open fully
                time.sleep(0.1) # Small pause before next cycle attempts reopen
                continue # Next loop iteration will try to open

            # Frame read was successful
            if self.stopped: # If it was previously stopped (e.g. due to read fail or disconnect)
                print(f"[Camera {self.src}] Resumed streaming successfully.")
                self.stopped = False # Mark as operational

            with self.lock:
                self.frame = frame_read.copy()
            
            time.sleep(1.0 / self.fps)

        # Exiting thread
        if self.cap.isOpened():
            self.cap.release()
        print(f"[Camera {self.src}] Update thread stopped.")


    def read(self):
        if self.stopped or self.frame is None: # If camera claims to be stopped or no frame yet
            return None
        with self.lock:
            # Make a copy to prevent issues if the frame is updated by the thread immediately after
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        print(f"[Camera {self.src}] Stop requested.")
        self.user_requested_stop = True # Signal thread to exit
        # Wait for the thread to finish, with a timeout
        if hasattr(self, '_update_thread') and self._update_thread.is_alive():
            self._update_thread.join(timeout=2.0) 
            if self._update_thread.is_alive():
                print(f"[Camera {self.src}] Warning: Update thread did not terminate in time.")
        
        self.stopped = True # Mark as stopped for external checks
        if self.cap.isOpened():
            self.cap.release()
        print(f"[Camera {self.src}] Resources released.")
