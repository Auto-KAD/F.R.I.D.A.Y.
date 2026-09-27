import cv2

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel
)

from vision.camera import Camera
from authentication.face_detector import FaceDetector
from authentication.face_recognizer import FaceRecognizer


class LockScreen(QWidget):

    authenticated_signal = pyqtSignal(str)

    def __init__(self):

        super().__init__()

        self.setWindowTitle("FRIDAY")

        self.camera = Camera()
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()

        if not self.face_recognizer.load():

            print(
                "ERROR: Could not load face recognition model."
            )

            self.camera.release()

            return

        self.authenticated = False
        self.authenticated_user = None

        self.setup_ui()

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.process_camera
        )

        self.timer.start(30)

    def setup_ui(self):

        layout = QVBoxLayout()

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        title = QLabel("FRIDAY")

        title.setFont(
            QFont(
                "Segoe UI",
                42,
                QFont.Weight.Bold
            )
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle = QLabel(
            "VISION AUTHENTICATION SYSTEM"
        )

        subtitle.setFont(
            QFont(
                "Segoe UI",
                14
            )
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # ---------------------------------
        # CAMERA PREVIEW
        # ---------------------------------

        self.camera_label = QLabel()

        self.camera_label.setFixedSize(
            640,
            360
        )

        self.camera_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.camera_label.setText(
            "Initializing camera..."
        )

        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #111820;
                border: 2px solid #303846;
                border-radius: 18px;
                color: #8f9baa;
                font-size: 14px;
            }
        """)

        # ---------------------------------
        # STATUS
        # ---------------------------------

        self.status = QLabel(
            "🔒  SYSTEM LOCKED"
        )

        self.status.setFont(
            QFont(
                "Segoe UI",
                18
            )
        )

        self.status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.instruction = QLabel(
            "Look at the camera to unlock FRIDAY"
        )

        self.instruction.setFont(
            QFont(
                "Segoe UI",
                13
            )
        )

        self.instruction.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # ---------------------------------
        # ADD EVERYTHING
        # ---------------------------------

        layout.addWidget(title)

        layout.addWidget(subtitle)

        layout.addSpacing(25)

        layout.addWidget(
            self.camera_label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        layout.addSpacing(20)

        layout.addWidget(self.status)

        layout.addWidget(self.instruction)

        self.setLayout(layout)

        # ---------------------------------
        # WINDOW STYLE
        # ---------------------------------

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f14;
                color: white;
            }

            QLabel {
                color: #e8f0ff;
            }
        """)

    def process_camera(self):

        if self.authenticated:
            return

        frame = self.camera.read()

        if frame is None:
            return

        # ---------------------------------
        # FACE DETECTION
        # ---------------------------------

        faces = self.face_detector.detect(frame)

        # Draw detected faces on preview

        display_frame = frame.copy()

        for (x, y, w, h) in faces:

            cv2.rectangle(
                display_frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                display_frame,
                "FACE",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        # ---------------------------------
        # DISPLAY CAMERA FRAME
        # ---------------------------------

        rgb_frame = cv2.cvtColor(
            display_frame,
            cv2.COLOR_BGR2RGB
        )

        height, width, channels = rgb_frame.shape

        bytes_per_line = channels * width

        qt_image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )

        pixmap = QPixmap.fromImage(
            qt_image
        )

        pixmap = pixmap.scaled(
            self.camera_label.width(),
            self.camera_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.camera_label.setPixmap(
            pixmap
        )

        # ---------------------------------
        # NO FACE
        # ---------------------------------

        if len(faces) == 0:

            self.status.setText(
                "🔒  SYSTEM LOCKED"
            )

            self.instruction.setText(
                "Look at the camera to unlock FRIDAY"
            )

            return

        # ---------------------------------
        # MULTIPLE FACES
        # ---------------------------------

        if len(faces) > 1:

            self.status.setText(
                "⚠️  MULTIPLE FACES DETECTED"
            )

            self.instruction.setText(
                "Only one person can authenticate"
            )

            return

        # ---------------------------------
        # SINGLE FACE
        # ---------------------------------

        x, y, w, h = faces[0]

        face = frame[
            y:y + h,
            x:x + w
        ]

        if face.size == 0:
            return

        gray_face = cv2.cvtColor(
            face,
            cv2.COLOR_BGR2GRAY
        )

        name, confidence = (
            self.face_recognizer.predict(
                gray_face
            )
        )

        self.status.setText(
            "🔍  AUTHENTICATING..."
        )

        self.instruction.setText(
            f"Face confidence: {confidence:.2f}"
        )

        # ---------------------------------
        # AUTHENTICATION SUCCESS
        # ---------------------------------

        if confidence < 70:

            self.authenticated = True

            self.authenticated_user = name

            self.status.setText(
                "🔓  ACCESS GRANTED"
            )

            self.instruction.setText(
                f"Welcome, {name}"
            )

            QTimer.singleShot(
                1000,
                self.authentication_success
            )

    def authentication_success(self):

        self.timer.stop()

        self.camera.release()

        self.authenticated_signal.emit(
            self.authenticated_user
        )

        self.close()

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_F11:

            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

        elif event.key() == Qt.Key.Key_Escape:

            if self.isFullScreen():
                self.showNormal()

        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):

        if hasattr(
            self,
            "timer"
        ):

            self.timer.stop()

        if hasattr(
            self,
            "camera"
        ):

            self.camera.release()

        event.accept()