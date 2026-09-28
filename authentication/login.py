import cv2

from vision.camera import Camera
from authentication.face_detector import FaceDetector
from authentication.face_recognizer import FaceRecognizer


# Lower LBPH distance = better match.
# Start conservatively and adjust after testing.
RECOGNITION_THRESHOLD = 60

# Number of consecutive successful frames required.
REQUIRED_MATCHES = 8


def main():

    print("=" * 50)
    print("             FRIDAY LOGIN")
    print("=" * 50)

    camera = Camera()
    detector = FaceDetector()
    recognizer = FaceRecognizer()

    print()
    print("Loading face recognition model...")

    if not recognizer.load():

        print("Could not load face recognition model.")

        camera.release()
        return

    print("Face recognition ready.")
    print("Look at the camera.")
    print("Press Q to quit.")
    print()

    matched_name = None
    match_count = 0

    while True:

        frame = camera.read()

        if frame is None:

            print("ERROR: Could not read camera frame.")
            break

        faces = detector.detect(frame)

        # -----------------------------------------
        # NO FACE
        # -----------------------------------------

        if len(faces) == 0:

            match_count = 0
            matched_name = None

            label = "FRIDAY LOCKED"
            text_color = (0, 0, 255)

            cv2.putText(
                frame,
                label,
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                text_color,
                2
            )

        # -----------------------------------------
        # MULTIPLE FACES
        # -----------------------------------------

        elif len(faces) > 1:

            match_count = 0
            matched_name = None

            label = "ONLY ONE USER ALLOWED"
            text_color = (0, 0, 255)

            cv2.putText(
                frame,
                label,
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                text_color,
                2
            )

        # -----------------------------------------
        # EXACTLY ONE FACE
        # -----------------------------------------

        else:

            x, y, w, h = faces[0]

            face = frame[
                y:y + h,
                x:x + w
            ]

            name, confidence = recognizer.predict(
                face
            )

            is_match = (
                name != "Unknown"
                and confidence < RECOGNITION_THRESHOLD
            )

            # -------------------------------------
            # SUCCESSFUL MATCH
            # -------------------------------------

            if is_match:

                if matched_name == name:

                    match_count += 1

                else:

                    matched_name = name
                    match_count = 1

                if match_count >= REQUIRED_MATCHES:

                    label = f"ACCESS GRANTED: {name}"
                    text_color = (0, 255, 0)

                else:

                    label = (
                        f"VERIFYING {name}: "
                        f"{match_count}/{REQUIRED_MATCHES}"
                    )

                    text_color = (0, 255, 255)

            # -------------------------------------
            # FAILED MATCH
            # -------------------------------------

            else:

                matched_name = None
                match_count = 0

                label = "ACCESS DENIED: UNKNOWN"
                text_color = (0, 0, 255)

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                text_color,
                2
            )

            cv2.putText(
                frame,
                label,
                (x, max(y - 10, 30)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                text_color,
                2
            )

            cv2.putText(
                frame,
                f"Distance: {confidence:.2f}",
                (x, y + h + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                text_color,
                2
            )

        cv2.imshow(
            "FRIDAY - Face Login",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    print("FRIDAY login stopped.")


if __name__ == "__main__":
    main()