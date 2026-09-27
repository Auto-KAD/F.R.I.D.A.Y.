import cv2
import time

from camera import Camera
from hand_tracker import HandTracker
from finger_detector import FingerDetector
from gesture_classifier import GestureClassifier
from gesture_stabilizer import GestureStabilizer
from gesture_actions import GestureActionController

def main():

    camera = Camera()

    tracker = HandTracker()

    finger_detector = FingerDetector()

    gesture_classifier = GestureClassifier()

    gesture_stabilizer = GestureStabilizer(
        required_frames=6
    )

    gesture_actions = GestureActionController()

    previous_time = time.time()

    try:

        while True:

            frame = camera.read()

            if frame is None:
                continue

            result = tracker.process(frame)

            frame = tracker.draw_landmarks(
                frame,
                result
            )

            hand_count = (
                len(result.hand_landmarks)
                if result.hand_landmarks
                else 0
            )

            confirmed_gesture = "UNKNOWN"

            if result.hand_landmarks:

                # Use first detected hand
                hand_landmarks = (
                    result.hand_landmarks[0]
                )

                # -------------------------
                # FINGER DETECTION
                # -------------------------

                fingers = (
                    finger_detector.detect_fingers(
                        hand_landmarks
                    )
                )

                finger_count = (
                    finger_detector.count_fingers(
                        fingers
                    )
                )

                finger_state = (
                    finger_detector.get_finger_state(
                        fingers
                    )
                )

                # -------------------------
                # GESTURE CLASSIFICATION
                # -------------------------

                raw_gesture = (
                    gesture_classifier.classify(
                        fingers,
                        hand_landmarks
                    )
                )

                # -------------------------
                # GESTURE STABILIZATION
                # -------------------------

                confirmed_gesture = (
                    gesture_stabilizer.update(
                        raw_gesture
                    )
                )

                # -------------------------
                # INDEX FINGERTIP
                # -------------------------

                index_tip = hand_landmarks[8]

                height, width, _ = frame.shape

                index_x = int(
                    index_tip.x * width
                )

                index_y = int(
                    index_tip.y * height
                )

                # Draw index fingertip

                cv2.circle(
                    frame,
                    (index_x, index_y),
                    10,
                    (0, 0, 255),
                    -1
                )

                cv2.putText(
                    frame,
                    f"INDEX ({index_x}, {index_y})",
                    (index_x + 15, index_y - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )

                # -------------------------
                # GESTURE ACTION
                # -------------------------

                gesture_actions.execute(
                    confirmed_gesture,
                    index_tip
                )

                # -------------------------
                # DISPLAY FINGER STATES
                # -------------------------

                y_position = 120

                for name, state in fingers.items():

                    status = (
                        "UP"
                        if state
                        else "DOWN"
                    )

                    cv2.putText(
                        frame,
                        f"{name}: {status}",
                        (20, y_position),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (255, 255, 255),
                        2
                    )

                    y_position += 30

                # Finger count

                cv2.putText(
                    frame,
                    f"FINGERS: {finger_count}",
                    (20, 285),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )

                # Finger state

                cv2.putText(
                    frame,
                    f"STATE: {finger_state}",
                    (20, 320),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )

                # Raw gesture

                cv2.putText(
                    frame,
                    f"RAW: {raw_gesture}",
                    (20, 360),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (255, 255, 0),
                    2
                )

                # Confirmed gesture

                cv2.putText(
                    frame,
                    f"GESTURE: {confirmed_gesture}",
                    (20, 400),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2
                )

            else:

                gesture_stabilizer.reset()

                gesture_actions.reset()

                cv2.putText(
                    frame,
                    "NO HAND",
                    (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            # -------------------------
            # FPS
            # -------------------------

            current_time = time.time()

            fps = 1 / max(
                current_time - previous_time,
                0.001
            )

            previous_time = current_time

            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"HANDS: {hand_count}",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            # -------------------------
            # CAMERA WINDOW
            # -------------------------

            cv2.imshow(
                "FRIDAY - Gesture Control",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:
                break

    finally:

        tracker.close()

        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()