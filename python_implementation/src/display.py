import cv2
import time

class DisplayWindow:
    def __init__(self, window_name):
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def show(self, frame, bbox=None, score=None, fps=None):
        disp_frame = frame.copy()
        if bbox is not None and score is not None:
            x, y, w, h = bbox
            cv2.rectangle(disp_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label = f"Person: {score:.2f}"
            cv2.putText(disp_frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if fps is not None:
            cv2.putText(disp_frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.imshow(self.window_name, disp_frame)

    def close(self):
        cv2.destroyWindow(self.window_name)
