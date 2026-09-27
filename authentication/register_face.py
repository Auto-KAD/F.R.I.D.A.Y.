import cv2
import os

from vision.camera import Camera
from authentication.face_detector import FaceDetector


def register_user():

    name = input("Enter user name: ").strip()

    if not name:
        print("Invalid name.")
        return

    save_path = os.path.join(
        "data",
        "faces",
        name
    )

    os.makedirs(
        save_path,
        exist_ok=True
    )

    camera = Camera()
    detector = FaceDetector()

    count = 0
    max_images = 20

    print()
    print("===================================")
    print("       FRIDAY FACE REGISTRATION")
    print("===================================")
    print()
    print("Look at the camera.")
    print("Move your face slightly.")
    print("Press Q to cancel.")
    print()

    while count < max_images:

        frame = camera.read()

        if frame is None:
            break

        faces = detector.detect(frame)

        if len(faces) == 1:

            x, y, w, h = faces[0]

            face = frame[y:y + h, x:x + w]

            gray_face = cv2.cvtColor(
                face,
                cv2.COLOR_BGR2GRAY
            )

            file_path = os.path.join(
                save_path,
                f"{count + 1}.jpg"
            )

            cv2.imwrite(
                file_path,
                gray_face
            )

            count += 1

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Captured: {count}/{max_images}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        else:

            cv2.putText(
                frame,
                "Keep exactly ONE face visible",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        cv2.imshow(
            "FRIDAY - Face Registration",
            frame
        )

        key = cv2.waitKey(300) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    print()
    print(f"Registration complete.")
    print(f"Images saved: {count}")
    print(f"User: {name}")


if __name__ == "__main__":
    register_user()