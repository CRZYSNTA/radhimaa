"""
=============================================================================
JARVIS Stage 2: Air-Gesture Virtual Mouse (Computer Vision - MediaPipe 1.0+)
=============================================================================
Goal: Control your screen mouse using webcam hand tracking.
 - Index finger moves cursor smoothly across screen
 - Pinching Index Finger + Thumb performs Left Click
 - Pinching Middle Finger + Thumb performs Right Click

Supports MediaPipe 1.0+ (HandLandmarker API) and legacy mp.solutions fallback.

Author: Built for beginners (B.Tech CS background)
=============================================================================
"""

import os
import math
import time
import urllib.request
import cv2
import numpy as np

# Safety Check: Import PyAutoGUI with FailSafe enabled
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Slamming mouse to screen corner stops script
    pyautogui.PAUSE = 0.01     # Reduces click delay
except ImportError:
    pyautogui = None

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError:
    mp = None

MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

def ensure_model_exists():
    """Downloads hand_landmarker.task model if missing."""
    if not os.path.exists(MODEL_PATH):
        print("⏳ Downloading MediaPipe Hand Tracker model (8 MB)...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("✅ Model downloaded successfully!")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")

class GestureMouse:
    def __init__(self):
        # Screen Dimensions
        if pyautogui:
            self.screen_w, self.screen_h = pyautogui.size()
        else:
            self.screen_w, self.screen_h = 1920, 1080

        # Movement smoothing state
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = 4  # Higher = smoother movement

        # Click state flags
        self.last_click_time = 0
        self.click_cooldown = 0.4  # seconds between clicks

        # MediaPipe Hand Detector Setup
        self.detector = None
        self.use_new_api = False

        if mp:
            ensure_model_exists()
            if os.path.exists(MODEL_PATH):
                try:
                    # MediaPipe 1.0+ HandLandmarker API
                    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
                    options = vision.HandLandmarkerOptions(
                        base_options=base_options,
                        num_hands=1,
                        min_hand_detection_confidence=0.6,
                        min_hand_presence_confidence=0.6
                    )
                    self.detector = vision.HandLandmarker.create_from_options(options)
                    self.use_new_api = True
                    print("✅ MediaPipe 1.0+ HandLandmarker initialized.")
                except Exception as e:
                    print(f"⚠️ HandLandmarker init error: {e}")

            if not self.detector and hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
                # Legacy MediaPipe API
                self.mp_hands = mp.solutions.hands
                self.detector = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.6,
                    min_tracking_confidence=0.6
                )
                self.mp_draw = mp.solutions.drawing_utils
                self.use_new_api = False
                print("✅ Legacy MediaPipe Hands initialized.")

    def calculate_distance(self, p1, p2):
        """Calculates Euclidean distance between two 2D points."""
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    def run(self):
        """Main loop capturing webcam feed and mapping hand movements to cursor."""
        if not self.detector or not pyautogui:
            print("❌ MediaPipe or PyAutoGUI not configured correctly.")
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open webcam.")
            return

        print("==========================================================")
        print("   🖐️ AIR-GESTURE VIRTUAL MOUSE STARTED")
        print("   - Move Index Finger: Move Mouse Cursor")
        print("   - Pinch Index + Thumb: Left Click")
        print("   - Pinch Middle + Thumb: Right Click")
        print("   - Slam cursor to corner or press 'q' to stop.")
        print("==========================================================")

        while True:
            success, frame = cap.read()
            if not success:
                break

            # Flip frame horizontally for mirror reflection
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            status_text = "Tracking Hand..."
            landmarks_list = []

            if self.use_new_api:
                # Process frame using MediaPipe 1.0+ Image object
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                detection_result = self.detector.detect(mp_image)
                if detection_result.hand_landmarks:
                    landmarks_list = detection_result.hand_landmarks[0]
            else:
                # Process using Legacy MediaPipe API
                results = self.detector.process(rgb_frame)
                if results.multi_hand_landmarks:
                    landmarks_list = results.multi_hand_landmarks[0].landmark

            if landmarks_list:
                # Convert normalized (0-1) coordinates to image pixel coordinates
                # Landmark 4: Thumb Tip | Landmark 8: Index Tip | Landmark 12: Middle Tip
                thumb_tip = (int(landmarks_list[4].x * w), int(landmarks_list[4].y * h))
                index_tip = (int(landmarks_list[8].x * w), int(landmarks_list[8].y * h))
                middle_tip = (int(landmarks_list[12].x * w), int(landmarks_list[12].y * h))

                # Draw joint points on webcam overlay
                cv2.circle(frame, index_tip, 8, (255, 0, 0), cv2.FILLED)
                cv2.circle(frame, thumb_tip, 8, (0, 255, 255), cv2.FILLED)
                cv2.circle(frame, middle_tip, 8, (0, 0, 255), cv2.FILLED)
                cv2.line(frame, index_tip, thumb_tip, (255, 255, 0), 2)

                # 1. Map Index Finger position to Screen Coordinates
                margin = 80
                target_x = np.interp(index_tip[0], (margin, w - margin), (0, self.screen_w))
                target_y = np.interp(index_tip[1], (margin, h - margin), (0, self.screen_h))

                # Exponential Moving Average Smoothing
                curr_x = self.prev_x + (target_x - self.prev_x) / self.smooth_factor
                curr_y = self.prev_y + (target_y - self.prev_y) / self.smooth_factor

                try:
                    pyautogui.moveTo(curr_x, curr_y)
                except pyautogui.FailSafeException:
                    print("⚠️ PyAutoGUI FailSafe Triggered. Mouse stopped.")
                    cap.release()
                    cv2.destroyAllWindows()
                    return

                self.prev_x, self.prev_y = curr_x, curr_y

                # 2. Detect Pinch Gestures
                dist_index_thumb = self.calculate_distance(index_tip, thumb_tip)
                dist_middle_thumb = self.calculate_distance(middle_tip, thumb_tip)
                current_time = time.time()

                # Left Click Pinch (Index + Thumb distance < 35 pixels)
                if dist_index_thumb < 35:
                    if current_time - self.last_click_time > self.click_cooldown:
                        pyautogui.click()
                        self.last_click_time = current_time
                        status_text = "ACTION: LEFT CLICK!"
                        cv2.circle(frame, index_tip, 16, (0, 255, 0), cv2.FILLED)

                # Right Click Pinch (Middle + Thumb distance < 35 pixels)
                elif dist_middle_thumb < 35:
                    if current_time - self.last_click_time > self.click_cooldown:
                        pyautogui.rightClick()
                        self.last_click_time = current_time
                        status_text = "ACTION: RIGHT CLICK!"
                        cv2.circle(frame, middle_tip, 16, (0, 0, 255), cv2.FILLED)
                else:
                    status_text = f"Cursor: ({int(curr_x)}, {int(curr_y)})"

            # Display status text overlay on feedback window
            cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.putText(frame, "Press 'q' to exit", (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            cv2.imshow("JARVIS Air-Gesture Control Window", frame)

            # Exit loop if 'q' key is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    mouse = GestureMouse()
    mouse.run()
