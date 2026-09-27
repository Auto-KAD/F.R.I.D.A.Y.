import time

import cv2

from PyQt6.QtCore import QThread, pyqtSignal

from vision.camera import Camera
from vision.hand_tracker import HandTracker
from vision.finger_detector import FingerDetector
from vision.gesture_classifier import GestureClassifier
from vision.gesture_stabilizer import GestureStabilizer
from vision.gesture_actions import GestureActionController


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

        self.last_emitted_gesture = "UNKNOWN"

    def run(self):
        try:
            self.camera = Camera()
            self.tracker = HandTracker()
            self.finger_detector = FingerDetector()
            self.gesture_classifier = GestureClassifier()
            self.gesture_stabilizer = GestureStabilizer(
                required_frames=6
            )
            self.gesture_actions = GestureActionController()

            while self.running:

                frame = self.camera.read()

                if frame is None:
                    continue

                result = self.tracker.process(frame)

                preview_frame = self.tracker.draw_landmarks(
                    frame.copy(),
                    result
                )

                if result.hand_landmarks:

                    hand_landmarks = result.hand_landmarks[0]

                    fingers = self.finger_detector.detect_fingers(
                        hand_landmarks
                    )

                    raw_gesture = self.gesture_classifier.classify(
                        fingers,
                        hand_landmarks
                    )

                    confirmed_gesture = self.gesture_stabilizer.update(
                        raw_gesture
                    )

                    index_tip = hand_landmarks[8]

                    self.gesture_actions.execute(
                        confirmed_gesture,
                        index_tip
                    )

                    if (
                        confirmed_gesture != "UNKNOWN"
                        and confirmed_gesture != self.last_emitted_gesture
                    ):
                        self.last_emitted_gesture = confirmed_gesture

                        self.gesture_detected.emit(
                            confirmed_gesture
                        )

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
                    self.last_emitted_gesture = "UNKNOWN"

                rgb_frame = cv2.cvtColor(
                    preview_frame,
                    cv2.COLOR_BGR2RGB
                )

                self.camera_frame.emit(
                    rgb_frame.copy()
                )

                time.sleep(0.005)

        except Exception as error:

            message = str(error)

            print(
                "Gesture worker error:",
                message
            )

            self.error_occurred.emit(
                message
            )

        finally:

            if self.tracker is not None:
                self.tracker.close()

            if self.camera is not None:
                self.camera.release()

    def stop(self):

        self.running = False

        if self.isRunning():
            self.wait()
