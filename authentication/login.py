import cv2

from vision.camera import Camera
from authentication.face_detector import FaceDetector
from authentication.face_recognizer import FaceRecognizer


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

    while True:

        frame = camera.read()

        if frame is None:
            print("ERROR: Could not read camera frame.")
            break

        faces = detector.detect(frame)

        if len(faces) == 0:

            cv2.putText(
                frame,
                "FRIDAY LOCKED",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        elif len(faces) > 1:

            cv2.putText(
                frame,
                "ONLY ONE USER ALLOWED",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        else:

            x, y, w, h = faces[0]

            face = frame[y:y + h, x:x + w]

            gray_face = cv2.cvtColor(
                face,
                cv2.COLOR_BGR2GRAY
            )

            name, confidence = recognizer.predict(
                gray_face
            )

            # LBPH confidence:
            # lower = better match
            if confidence < 70:

                label = f"ACCESS GRANTED: {name}"
                text_color = (0, 255, 0)

            else:

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
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                text_color,
                2
            )

            cv2.putText(
                frame,
                f"Confidence: {confidence:.2f}",
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