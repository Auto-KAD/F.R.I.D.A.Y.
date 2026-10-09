import os
import time
import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandTracker:

    def __init__(
        self,
        model_path="models/hand_landmarker.task",
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    ):

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Hand Landmarker model not found: {model_path}"
            )

        base_options = python.BaseOptions(
            model_asset_path=model_path
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_hand_presence_confidence=min_hand_presence_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

        self.landmarker = vision.HandLandmarker.create_from_options(
            options
        )
        self._last_timestamp_ms = -1

    def process(self, frame, timestamp_ms=None):

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        if timestamp_ms is None:
            timestamp_ms = time.monotonic_ns() // 1_000_000

        timestamp_ms = max(
            int(timestamp_ms),
            self._last_timestamp_ms + 1
        )
        self._last_timestamp_ms = timestamp_ms

        result = self.landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

        return result

    def get_index_fingertips(self, result):

        fingertips = []

        if not result.hand_landmarks:
            return fingertips

        for hand_landmarks in result.hand_landmarks:

            index_tip = hand_landmarks[8]

            fingertips.append({
                "x": index_tip.x,
                "y": index_tip.y,
                "z": index_tip.z
            })

        return fingertips

    def draw_landmarks(self, frame, result):

        if not result.hand_landmarks:
            return frame

        height, width, _ = frame.shape

        for hand_landmarks in result.hand_landmarks:

            points = []

            for landmark in hand_landmarks:

                x = int(landmark.x * width)
                y = int(landmark.y * height)

                points.append((x, y))

                cv2.circle(
                    frame,
                    (x, y),
                    4,
                    (0, 255, 0),
                    -1
                )

            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (0, 5), (5, 6), (6, 7), (7, 8),
                (0, 9), (9, 10), (10, 11), (11, 12),
                (0, 13), (13, 14), (14, 15), (15, 16),
                (0, 17), (17, 18), (18, 19), (19, 20),
                (5, 9),
                (9, 13),
                (13, 17)
            ]

            for start, end in connections:

                cv2.line(
                    frame,
                    points[start],
                    points[end],
                    (0, 255, 0),
                    2
                )

        return frame

    def close(self):

        self.landmarker.close()