import time

import cv2
from PyQt6.QtCore import QThread, pyqtSignal

from vision.camera import Camera
from vision.hand_tracker import HandTracker
from vision.finger_detector import FingerDetector
from vision.gesture_classifier import GestureClassifier
from vision.gesture_stabilizer import GestureStabilizer
from vision.gesture_actions import GestureActionController, TRACKING_REGION


class DesktopGestureWorker(QThread):
    """Runs FRIDAY hand/gesture recognition without blocking the Qt UI."""

    gesture_detected = pyqtSignal(str)
    camera_frame = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.running = True
        self.camera = None
        self.tracker = None
        self.finger_detector = None
        self.gesture_classifier = None
        self.gesture_stabilizer = None
        self.gesture_actions = None

        self.two_thumbs_streak = 0
        self.last_emitted_gesture = "UNKNOWN"

    def run(self):
        try:
            self.camera = Camera()
            self.tracker = HandTracker()
            self.finger_detector = FingerDetector()
            self.gesture_classifier = GestureClassifier()
            self.gesture_stabilizer = GestureStabilizer(
                required_frames=4
            )
            self.gesture_actions = GestureActionController()

            while self.running:
                frame = self.camera.read()
                if frame is None:
                    time.sleep(0.005)
                    continue

                result = self.tracker.process(frame)
                preview_frame = self.tracker.draw_landmarks(
                    frame.copy(),
                    result
                )
                height, width, _ = preview_frame.shape
                left, right, top, bottom = TRACKING_REGION
                region_start = (int(left * width), int(top * height))
                region_end = (int(right * width), int(bottom * height))
                cv2.rectangle(
                    preview_frame,
                    region_start,
                    region_end,
                    (104, 140, 111),
                    2
                )
                cv2.putText(
                    preview_frame,
                    "POINTER ACTIVE AREA",
                    (region_start[0] + 8, region_start[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (104, 140, 111),
                    2
                )

                hand_landmarks_list = result.hand_landmarks or []
                hand_gestures = []

                for hand_landmarks in hand_landmarks_list:
                    fingers = self.finger_detector.detect_fingers(
                        hand_landmarks
                    )
                    hand_gestures.append(
                        self.gesture_classifier.classify(
                            fingers,
                            hand_landmarks
                        )
                    )

                both_thumbs_up = (
                    len(hand_gestures) >= 2
                    and hand_gestures[0] == "THUMBS_UP"
                    and hand_gestures[1] == "THUMBS_UP"
                )

                if both_thumbs_up:
                    self.two_thumbs_streak += 1
                    self.gesture_stabilizer.reset()
                    self.gesture_actions.reset()

                    if (
                        self.two_thumbs_streak >= 6
                        and self.last_emitted_gesture != "TWO_THUMBS_UP"
                    ):
                        self.last_emitted_gesture = "TWO_THUMBS_UP"
                        self.gesture_detected.emit("TWO_THUMBS_UP")

                    cv2.putText(
                        preview_frame,
                        "TWO THUMBS UP - SCREENSHOT",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )

                elif hand_landmarks_list:
                    self.two_thumbs_streak = 0
                    hand_landmarks = hand_landmarks_list[0]
                    raw_gesture = hand_gestures[0]

                    confirmed_gesture = self.gesture_stabilizer.update(
                        raw_gesture
                    )

                    index_tip = hand_landmarks[8]
                    action_gesture = (
                        raw_gesture
                        if raw_gesture == "POINT"
                        else confirmed_gesture
                    )
                    self.gesture_actions.execute(
                        action_gesture,
                        index_tip
                    )

                    if (
                        confirmed_gesture != "UNKNOWN"
                        and confirmed_gesture != self.last_emitted_gesture
                    ):
                        self.last_emitted_gesture = confirmed_gesture
                        self.gesture_detected.emit(confirmed_gesture)

                    height, width, _ = preview_frame.shape
                    index_x = int(index_tip.x * width)
                    index_y = int(index_tip.y * height)

                    cv2.circle(
                        preview_frame,
                        (index_x, index_y),
                        10,
                        (0, 0, 255),
                        -1
                    )
                    cv2.putText(
                        preview_frame,
                        "INDEX",
                        (index_x + 12, index_y - 12),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 0, 255),
                        2
                    )

                else:
                    self.gesture_stabilizer.reset()
                    self.gesture_actions.reset()
                    self.two_thumbs_streak = 0
                    self.last_emitted_gesture = "UNKNOWN"

                rgb_frame = cv2.cvtColor(
                    preview_frame,
                    cv2.COLOR_BGR2RGB
                )
                self.camera_frame.emit(rgb_frame.copy())
                time.sleep(0.005)

        except Exception as error:
            message = str(error)
            print("Gesture worker error:", message)
            self.error_occurred.emit(message)

        finally:
            if self.tracker is not None:
                self.tracker.close()
            if self.camera is not None:
                self.camera.release()

    def stop(self):
        self.running = False
        if self.isRunning():
            self.wait()
