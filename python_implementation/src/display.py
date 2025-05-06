import cv2
import time

class DisplayWindow:
    def __init__(self, window_name):
        self.window_name = window_name
        # cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL) # Moved to main.py

    def draw_overlays(self, frame, bbox=None, score=None, fps=None):
        """Draws bounding boxes, scores, and FPS on the frame."""
        disp_frame = frame.copy()
        # Frame is grayscale. Colors will be shades of gray.
        # Using (255) for white, or other scalar values for shades of gray.
        overlay_color = (255) # White for overlays

        if bbox is not None and score is not None:
            # Ensure bbox coordinates are integers
            x, y, w, h = map(int, bbox)
            cv2.rectangle(disp_frame, (x, y), (x + w, y + h), overlay_color, 2)
            label = f"Person: {score:.2f}"
            cv2.putText(disp_frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, overlay_color, 2)
        if fps is not None:
            # For FPS text, also use a grayscale color. White should be fine.
            cv2.putText(disp_frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, overlay_color, 2)
        # cv2.imshow(self.window_name, disp_frame) # Removed - display handled externally
        return disp_frame # Return the annotated frame

    def create_window(self):
        """Creates the display window."""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def close(self):
        """Closes the specific display window."""
        cv2.destroyWindow(self.window_name)
