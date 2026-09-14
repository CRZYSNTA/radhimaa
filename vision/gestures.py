"""
JARVIS Vision - Air-Gesture Virtual Mouse
MediaPipe hand tracking -> PyAutoGUI mouse control
"""
import os
import math
import time
import threading
import urllib.request
import cv2
import numpy as np

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.01
except ImportError:
    pyautogui = None

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError:
    mp = None

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "hand_landmarker.task")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

_gesture_thread = None
_gesture_running = False

def ensure_model_exists():
    if not os.path.exists(MODEL_PATH):
        print("⏳ Downloading MediaPipe Hand Tracker model (8 MB)...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("✅ Model downloaded!")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")

class GestureMouse:
    def __init__(self):
        if pyautogui:
            self.screen_w, self.screen_h = pyautogui.size()
        else:
            self.screen_w, self.screen_h = 1920, 1080
        
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = 4
        self.last_click_time = 0
        self.click_cooldown = 0.4
        self.detector = None
        self.use_new_api = False
        
        if mp:
            ensure_model_exists()
            if os.path.exists(MODEL_PATH):
                try:
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
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    
    def run(self):
        if not self.detector or not pyautogui:
            print("❌ MediaPipe or PyAutoGUI not configured.")
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
        
        while _gesture_running:
            success, frame = cap.read()
            if not success:
                break
            
            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            landmarks_list = []
            
            if self.use_new_api:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                detection_result = self.detector.detect(mp_image)
                if detection_result.hand_landmarks:
                    landmarks_list = detection_result.hand_landmarks[0]
            else:
                results = self.detector.process(rgb_frame)
                if results.multi_hand_landmarks:
                    landmarks_list = results.multi_hand_landmarks[0].landmark
            
            if landmarks_list:
                thumb_tip = (int(landmarks_list[4].x * w), int(landmarks_list[4].y * h))
                index_tip = (int(landmarks_list[8].x * w), int(landmarks_list[8].y * h))
                middle_tip = (int(landmarks_list[12].x * w), int(landmarks_list[12].y * h))
                
                cv2.circle(frame, index_tip, 8, (255, 0, 0), cv2.FILLED)
                cv2.circle(frame, thumb_tip, 8, (0, 255, 255), cv2.FILLED)
                cv2.circle(frame, middle_tip, 8, (0, 0, 255), cv2.FILLED)
                cv2.line(frame, index_tip, thumb_tip, (255, 255, 0), 2)
                
                margin = 80
                target_x = np.interp(index_tip[0], (margin, w - margin), (0, self.screen_w))
                target_y = np.interp(index_tip[1], (margin, h - margin), (0, self.screen_h))
                
                curr_x = self.prev_x + (target_x - self.prev_x) / self.smooth_factor
                curr_y = self.prev_y + (target_y - self.prev_y) / self.smooth_factor
                
                try:
                    pyautogui.moveTo(curr_x, curr_y)
                except pyautogui.FailSafeException:
                    print("⚠️ PyAutoGUI FailSafe Triggered.")
                    break
                
                self.prev_x, self.prev_y = curr_x, curr_y
                
                dist_index_thumb = self.calculate_distance(index_tip, thumb_tip)
                dist_middle_thumb = self.calculate_distance(middle_tip, thumb_tip)
                current_time = time.time()
                
                if dist_index_thumb < 35:
                    if current_time - self.last_click_time > self.click_cooldown:
                        pyautogui.click()
                        self.last_click_time = current_time
                        cv2.circle(frame, index_tip, 16, (0, 255, 0), cv2.FILLED)
                
                elif dist_middle_thumb < 35:
                    if current_time - self.last_click_time > self.click_cooldown:
                        pyautogui.rightClick()
                        self.last_click_time = current_time
                        cv2.circle(frame, middle_tip, 16, (0, 0, 255), cv2.FILLED)
            
            cv2.putText(frame, "Press 'q' to exit", (20, h - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            cv2.imshow("JARVIS Air-Gesture Control", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

def start_gesture_mouse() -> str:
    global _gesture_thread, _gesture_running
    if _gesture_running:
        return "Gesture mouse already running."
    
    _gesture_running = True
    mouse = GestureMouse()
    _gesture_thread = threading.Thread(target=mouse.run, daemon=True)
    _gesture_thread.start()
    return "Air-gesture virtual mouse started, sir."

def stop_gesture_mouse() -> str:
    global _gesture_running, _gesture_thread
    _gesture_running = False
    if _gesture_thread:
        _gesture_thread.join(timeout=2)
    return "Air-gesture virtual mouse stopped, sir."

if __name__ == "__main__":
    print(start_gesture_mouse())
    time.sleep(30)
    print(stop_gesture_mouse())