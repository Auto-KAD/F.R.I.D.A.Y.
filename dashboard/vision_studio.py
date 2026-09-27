import cv2

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame
)

from vision.camera import Camera


class VisionStudio(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "FRIDAY — Vision Studio"
        )

        self.setMinimumSize(
            1100,
            700
        )

        self.camera = None

        self.current_mode = "ORIGINAL"

        self.frame_count = 0
        self.previous_time = cv2.getTickCount()

        self.setup_ui()

        self.start_camera()

    # --------------------------------
    # UI
    # --------------------------------

    def setup_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            25,
            20,
            25,
            20
        )

        main_layout.setSpacing(
            15
        )

        # --------------------------------
        # HEADER
        # --------------------------------

        header_layout = QHBoxLayout()

        title = QLabel(
            "VISION STUDIO"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                28,
                QFont.Weight.Bold
            )
        )

        subtitle = QLabel(
            "Real-time image processing"
        )

        subtitle.setFont(
            QFont(
                "Segoe UI",
                11
            )
        )

        header_layout.addWidget(
            title
        )

        header_layout.addSpacing(
            15
        )

        header_layout.addWidget(
            subtitle
        )

        header_layout.addStretch()

        main_layout.addLayout(
            header_layout
        )

        # --------------------------------
        # CAMERA AREA
        # --------------------------------

        content_layout = QHBoxLayout()

        # Camera display
        camera_frame = QFrame()

        camera_frame.setObjectName(
            "cameraFrame"
        )

        camera_layout = QVBoxLayout()

        self.camera_label = QLabel(
            "Initializing camera..."
        )

        self.camera_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.camera_label.setMinimumSize(
            700,
            450
        )

        camera_layout.addWidget(
            self.camera_label
        )

        camera_frame.setLayout(
            camera_layout
        )

        content_layout.addWidget(
            camera_frame,
            1
        )

        # --------------------------------
        # PROCESSING CONTROLS
        # --------------------------------

        controls_frame = QFrame()

        controls_frame.setObjectName(
            "controlsFrame"
        )

        controls_layout = QVBoxLayout()

        controls_layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        mode_title = QLabel(
            "PROCESSING"
        )

        mode_title.setFont(
            QFont(
                "Segoe UI",
                14,
                QFont.Weight.Bold
            )
        )

        controls_layout.addWidget(
            mode_title
        )

        controls_layout.addSpacing(
            10
        )

        modes = [
            "ORIGINAL",
            "GRAYSCALE",
            "BLUR",
            "EDGE",
            "THRESHOLD",
            "SHARPEN",
            "HSV",
            "NEGATIVE"
        ]

        for mode in modes:

            button = QPushButton(
                mode
            )

            button.setFixedHeight(
                40
            )

            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            button.clicked.connect(
                lambda checked=False,
                selected_mode=mode:
                self.set_mode(selected_mode)
            )

            controls_layout.addWidget(
                button
            )

        controls_layout.addStretch()

        capture_button = QPushButton(
            "📸  CAPTURE"
        )

        capture_button.setFixedHeight(
            42
        )

        capture_button.clicked.connect(
            self.capture_image
        )

        controls_layout.addWidget(
            capture_button
        )

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setFixedHeight(
            42
        )

        close_button.clicked.connect(
            self.close
        )

        controls_layout.addWidget(
            close_button
        )

        controls_frame.setLayout(
            controls_layout
        )

        content_layout.addWidget(
            controls_frame
        )

        main_layout.addLayout(
            content_layout,
            1
        )

        # --------------------------------
        # INFORMATION BAR
        # --------------------------------

        info_frame = QFrame()

        info_frame.setObjectName(
            "infoFrame"
        )

        info_layout = QHBoxLayout()

        self.mode_label = QLabel(
            "MODE: ORIGINAL"
        )

        self.fps_label = QLabel(
            "FPS: --"
        )

        self.resolution_label = QLabel(
            "RESOLUTION: --"
        )

        info_layout.addWidget(
            self.mode_label
        )

        info_layout.addStretch()

        info_layout.addWidget(
            self.fps_label
        )

        info_layout.addSpacing(
            25
        )

        info_layout.addWidget(
            self.resolution_label
        )

        info_frame.setLayout(
            info_layout
        )

        main_layout.addWidget(
            info_frame
        )

        self.setLayout(
            main_layout
        )

        # --------------------------------
        # STYLE
        # --------------------------------

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f14;
                color: #e8f0ff;
            }

            QFrame#cameraFrame {
                background-color: #05080c;
                border: 1px solid #303a48;
                border-radius: 16px;
            }

            QFrame#controlsFrame {
                background-color: #111720;
                border: 1px solid #27313e;
                border-radius: 16px;
            }

            QFrame#infoFrame {
                background-color: #141b24;
                border: 1px solid #303a48;
                border-radius: 12px;
            }

            QPushButton {
                background-color: #1b2430;
                color: #e8f0ff;
                border: 1px solid #323d4c;
                border-radius: 10px;
                font-family: "Segoe UI";
                font-size: 11px;
                padding: 6px;
            }

            QPushButton:hover {
                background-color: #273342;
                border: 1px solid #566579;
            }

            QPushButton:pressed {
                background-color: #303d4d;
            }
        """)

    # --------------------------------
    # CAMERA
    # --------------------------------

    def start_camera(self):

        try:

            self.camera = Camera()

        except Exception as error:

            self.camera_label.setText(
                f"Camera error:\n{error}"
            )

            return

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.process_frame
        )

        self.timer.start(
            30
        )

    # --------------------------------
    # SET PROCESSING MODE
    # --------------------------------

    def set_mode(
        self,
        mode
    ):

        self.current_mode = mode

        self.mode_label.setText(
            f"MODE: {mode}"
        )

    # --------------------------------
    # PROCESS FRAME
    # --------------------------------

    def process_frame(self):

        if self.camera is None:
            return

        frame = self.camera.read()

        if frame is None:
            return

        processed_frame = self.apply_processing(
            frame
        )

        self.display_frame(
            processed_frame
        )

        # FPS
        self.frame_count += 1

        current_time = cv2.getTickCount()

        elapsed = (
            current_time
            - self.previous_time
        ) / cv2.getTickFrequency()

        if elapsed >= 1.0:

            fps = (
                self.frame_count
                / elapsed
            )

            self.fps_label.setText(
                f"FPS: {fps:.1f}"
            )

            self.frame_count = 0

            self.previous_time = (
                current_time
            )

        # Resolution
        height, width = frame.shape[:2]

        self.resolution_label.setText(
            f"RESOLUTION: {width} × {height}"
        )

    # --------------------------------
    # IMAGE PROCESSING
    # --------------------------------

    def apply_processing(
        self,
        frame
    ):

        if self.current_mode == "ORIGINAL":

            return frame

        # GRAYSCALE
        if self.current_mode == "GRAYSCALE":

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            return cv2.cvtColor(
                gray,
                cv2.COLOR_GRAY2BGR
            )

        # BLUR
        if self.current_mode == "BLUR":

            return cv2.GaussianBlur(
                frame,
                (15, 15),
                0
            )

        # EDGE
        if self.current_mode == "EDGE":

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            edges = cv2.Canny(
                gray,
                100,
                200
            )

            return cv2.cvtColor(
                edges,
                cv2.COLOR_GRAY2BGR
            )

        # THRESHOLD
        if self.current_mode == "THRESHOLD":

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            _, threshold = cv2.threshold(
                gray,
                127,
                255,
                cv2.THRESH_BINARY
            )

            return cv2.cvtColor(
                threshold,
                cv2.COLOR_GRAY2BGR
            )

        # SHARPEN
        if self.current_mode == "SHARPEN":

            kernel = cv2.getGaussianKernel(
                5,
                1
            )

            kernel = (
                kernel
                @ kernel.T
            )

            sharpen_kernel = (
                -kernel
            )

            sharpen_kernel[2, 2] += 2

            return cv2.filter2D(
                frame,
                -1,
                sharpen_kernel
            )

        # HSV
        if self.current_mode == "HSV":

            hsv = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2HSV
            )

            return hsv

        # NEGATIVE
        if self.current_mode == "NEGATIVE":

            return cv2.bitwise_not(
                frame
            )

        return frame

    # --------------------------------
    # DISPLAY FRAME
    # --------------------------------

    def display_frame(
        self,
        frame
    ):

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        height, width, channels = (
            rgb_frame.shape
        )

        bytes_per_line = (
            channels * width
        )

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

    # --------------------------------
    # CAPTURE IMAGE
    # --------------------------------

    def capture_image(self):

        if self.camera is None:
            return

        frame = self.camera.read()

        if frame is None:
            return

        processed_frame = self.apply_processing(
            frame
        )

        filename = (
            "vision_capture_"
            + str(
                cv2.getTickCount()
            )
            + ".png"
        )

        cv2.imwrite(
            filename,
            processed_frame
        )

        self.mode_label.setText(
            f"CAPTURED: {filename}"
        )

    # --------------------------------
    # FULLSCREEN CONTROLS
    # --------------------------------

    def keyPressEvent(
        self,
        event
    ):

        if event.key() == Qt.Key.Key_F11:

            if self.isFullScreen():

                self.showNormal()

            else:

                self.showFullScreen()

        elif event.key() == Qt.Key.Key_Escape:

            if self.isFullScreen():

                self.showNormal()

        else:

            super().keyPressEvent(
                event
            )

    # --------------------------------
    # CLOSE
    # --------------------------------

    def closeEvent(
        self,
        event
    ):

        if hasattr(
            self,
            "timer"
        ):

            self.timer.stop()

        if self.camera is not None:

            self.camera.release()

        event.accept()