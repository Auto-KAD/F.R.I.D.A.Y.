import cv2


class Camera:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera.")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def read(self):
        ret, frame = self.cap.read()

        if not ret:
            return None

        # Mirror the camera like a normal webcam
        frame = cv2.flip(frame, 1)

        return frame

    def release(self):
        self.cap.release()