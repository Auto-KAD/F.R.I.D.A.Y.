import os
import psutil
import pyautogui

from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPainterPath, QImage
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame
)

from dashboard.system_panel import SystemPanel
from dashboard.vision_studio import VisionStudio
from dashboard.media_controller import MediaController
from dashboard.tools import Tools
from dashboard.calendar import Calendar
from dashboard.chatbot import ChatbotPanel
from vision.desktop_gesture_worker import DesktopGestureWorker


class Desktop(QWidget):

    def __init__(self, username):

        super().__init__()

        self.username = username

        # ==================================================
        # APPLICATION WINDOWS
        # ==================================================

        self.system_panel = None
        self.vision_studio = None
        self.media_controller = None
        self.tools = None
        self.calendar = None

        # ==================================================
        # CHATBOT
        # ==================================================

        self.chatbot = None

        # ==================================================
        # GESTURE CONTROL
        # ==================================================

        self.gesture_worker = None

        # The Vision Studio can also need the physical camera.
        # This timer manages camera ownership between FRIDAY's
        # gesture worker and Vision Studio.
        self.camera_ownership_timer = None

        self.setWindowTitle("FRIDAY")

        self.setup_ui()

        self.start_system_monitor()
        self.start_gesture_control()
        self.start_camera_ownership_monitor()

    # ======================================================
    # MAIN UI
    # ======================================================

    def setup_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            28,
            20,
            28,
            18
        )

        main_layout.setSpacing(0)

        # ==================================================
        # TOP AREA
        # ==================================================

        top_area = QFrame()

        top_area.setObjectName("topArea")

        top_layout = QHBoxLayout()

        top_layout.setContentsMargins(
            12,
            8,
            12,
            8
        )

        # ==================================================
        # PROFILE — TOP LEFT
        # ==================================================

        profile_container = QFrame()

        profile_layout = QHBoxLayout()

        profile_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        profile_layout.setSpacing(10)

        self.profile_photo = QLabel()

        self.profile_photo.setFixedSize(
            54,
            54
        )

        self.profile_photo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.load_profile_photo()

        profile_text_layout = QVBoxLayout()

        profile_text_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        profile_text_layout.setSpacing(2)

        logged_label = QLabel(
            "LOGGED IN AS"
        )

        logged_label.setFont(
            QFont(
                "Segoe UI",
                8,
                QFont.Weight.Bold
            )
        )

        username_label = QLabel(
            self.username.upper()
        )

        username_label.setFont(
            QFont(
                "Segoe UI",
                12,
                QFont.Weight.Bold
            )
        )

        profile_text_layout.addWidget(
            logged_label
        )

        profile_text_layout.addWidget(
            username_label
        )

        profile_layout.addWidget(
            self.profile_photo
        )

        profile_layout.addLayout(
            profile_text_layout
        )

        profile_container.setLayout(
            profile_layout
        )

        top_layout.addWidget(
            profile_container
        )

        # ==================================================
        # RIGHT STATUS
        # ==================================================

        status_container = QFrame()

        status_layout = QVBoxLayout()

        status_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        status_layout.setSpacing(2)

        self.system_label = QLabel(
            "CPU  --%     RAM  --%"
        )

        self.system_label.setFont(
            QFont(
                "Segoe UI",
                9
            )
        )

        status_label = QLabel(
            "●  ONLINE"
        )

        status_label.setFont(
            QFont(
                "Segoe UI",
                9,
                QFont.Weight.Bold
            )
        )

        self.clock_label = QLabel(
            "--:--"
        )

        self.clock_label.setFont(
            QFont(
                "Segoe UI",
                9
            )
        )

        status_layout.addWidget(
            self.system_label,
            alignment=Qt.AlignmentFlag.AlignRight
        )

        status_layout.addWidget(
            status_label,
            alignment=Qt.AlignmentFlag.AlignRight
        )

        status_layout.addWidget(
            self.clock_label,
            alignment=Qt.AlignmentFlag.AlignRight
        )

        status_container.setLayout(
            status_layout
        )

        top_layout.addWidget(
            status_container
        )

        top_area.setLayout(
            top_layout
        )

        main_layout.addWidget(
            top_area
        )

        main_layout.addSpacing(12)

        # ==================================================
        # APPLICATION DOCK — TOP
        # ==================================================

        dock = QFrame()
        dock.setObjectName("dock")

        dock_layout = QHBoxLayout()
        dock_layout.setContentsMargins(18, 12, 18, 12)
        dock_layout.setSpacing(10)
        dock_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        applications = [
            ("🎵", "Music"),
            ("🎬", "Media"),
            ("👁", "Vision"),
            ("📅", "Calendar"),
            ("🛠", "Tools"),
            ("⚙", "System")
        ]

        for icon, name in applications:
            button = QPushButton(f"{icon}\n{name}")
            button.setFixedSize(105, 68)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

            if name == "System":
                button.clicked.connect(self.open_system_panel)
            elif name == "Vision":
                button.clicked.connect(self.open_vision_studio)
            elif name == "Media":
                button.clicked.connect(self.open_media_controller)
            elif name == "Tools":
                button.clicked.connect(self.open_tools)
            elif name == "Calendar":
                button.clicked.connect(self.open_calendar)

            dock_layout.addWidget(button)

        dock.setLayout(dock_layout)
        main_layout.addWidget(dock)
        main_layout.addSpacing(12)

        # ==================================================
        # CENTER AREA + CAMERA PREVIEW
        # ==================================================

        center_area = QFrame()
        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(20, 10, 20, 10)
        center_layout.setSpacing(30)

        welcome_area = QFrame()
        welcome_layout = QVBoxLayout()
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome = QLabel(f"WELCOME, {self.username.upper()}")
        welcome.setFont(QFont("Segoe UI", 34, QFont.Weight.Bold))
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)

        assistant_status = QLabel("FRIDAY SYSTEM ONLINE")
        assistant_status.setFont(QFont("Segoe UI", 15))
        assistant_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description = QLabel(
            "Your intelligent visual desktop environment\n\n"
            "Point ☝  Move cursor     Pinch 🤏  Click"
        )
        description.setFont(QFont("Segoe UI", 11))
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gesture_status_label = QLabel("GESTURE CONTROL • INITIALIZING")
        self.gesture_status_label.setFont(
            QFont("Segoe UI", 10, QFont.Weight.Bold)
        )
        self.gesture_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_layout.addWidget(welcome)
        welcome_layout.addSpacing(8)
        welcome_layout.addWidget(assistant_status)
        welcome_layout.addSpacing(8)
        welcome_layout.addWidget(description)
        welcome_layout.addSpacing(12)
        welcome_layout.addWidget(self.gesture_status_label)
        welcome_area.setLayout(welcome_layout)

        self.camera_preview = QLabel()
        self.camera_preview.setFixedSize(360, 230)
        self.camera_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_preview.setText("CAMERA\nSTARTING...")
        self.camera_preview.setObjectName("cameraPreview")

        center_layout.addWidget(welcome_area, 1)
        center_layout.addWidget(self.camera_preview, 0, Qt.AlignmentFlag.AlignCenter)
        center_area.setLayout(center_layout)

        main_layout.addWidget(center_area, 1)

        # ==================================================
        # FRIDAY HEADING — BOTTOM
        # ==================================================

        bottom_heading = QFrame()
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 8, 0, 4)
        bottom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        friday_title = QLabel("F.R.I.D.A.Y.")
        friday_title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        friday_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        friday_title.setObjectName("fridayTitle")

        bottom_subtitle = QLabel("VISION • GESTURE • INTELLIGENCE")
        bottom_subtitle.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        bottom_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bottom_layout.addWidget(friday_title)
        bottom_layout.addWidget(bottom_subtitle)
        bottom_heading.setLayout(bottom_layout)
        main_layout.addWidget(bottom_heading)


        self.setLayout(
            main_layout
        )

        # ==================================================
        # CHATBOT CIRCULAR BUTTON
        # ==================================================

        self.chatbot_button = QPushButton(
            "F",
            self
        )

        self.chatbot_button.setObjectName(
            "chatbotButton"
        )

        self.chatbot_button.setFixedSize(
            64,
            64
        )

        self.chatbot_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.chatbot_button.setToolTip(
            "Ask FRIDAY"
        )

        self.chatbot_button.clicked.connect(
            self.toggle_chatbot
        )

        self.chatbot_button.show()

        # ==================================================
        # STYLE
        # ==================================================

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f14;
                color: #e8f0ff;
            }

            QFrame#topArea {
                background-color: #111720;
                border: 1px solid #27313e;
                border-radius: 16px;
            }

            QLabel {
                background-color: transparent;
                color: #e8f0ff;
            }

            QLabel#fridayTitle {
                letter-spacing: 3px;
            }

            QLabel#cameraPreview {
                background-color: #05080c;
                border: 2px solid #344253;
                border-radius: 16px;
                color: #8997a8;
                font-family: "Segoe UI";
                font-size: 12px;
                font-weight: bold;
            }

            QFrame#dock {
                background-color: #141b24;
                border: 1px solid #303a48;
                border-radius: 24px;
            }

            QPushButton {
                background-color: #1b2430;
                color: #e8f0ff;
                border: 1px solid #323d4c;
                border-radius: 15px;
                font-family: "Segoe UI";
                font-size: 12px;
                padding: 5px;
            }

            QPushButton:hover {
                background-color: #273342;
                border: 1px solid #566579;
            }

            QPushButton:pressed {
                background-color: #303d4d;
            }

            QPushButton#chatbotButton {
                background-color: #1b2430;
                color: #ffffff;
                border: 2px solid #6d8097;
                border-radius: 32px;
                font-family: "Segoe UI";
                font-size: 24px;
                font-weight: bold;
                padding: 0px;
            }

            QPushButton#chatbotButton:hover {
                background-color: #273342;
                border: 2px solid #a8b6c7;
            }

            QPushButton#chatbotButton:pressed {
                background-color: #303d4d;
            }
        """)

        # Position after UI has been created
        self.position_chatbot_button()

    # ======================================================
    # PROFILE PHOTO
    # ======================================================

    def load_profile_photo(self):

        profile_path = os.path.join(
            "data",
            "profiles",
            f"{self.username}.png"
        )

        if not os.path.exists(profile_path):

            profile_path = os.path.join(
                "data",
                "profiles",
                f"{self.username}.jpg"
            )

        if os.path.exists(profile_path):

            pixmap = QPixmap(
                profile_path
            )

            if not pixmap.isNull():

                pixmap = pixmap.scaled(
                    54,
                    54,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )

                circular_pixmap = QPixmap(
                    54,
                    54
                )

                circular_pixmap.fill(
                    Qt.GlobalColor.transparent
                )

                painter = QPainter(
                    circular_pixmap
                )

                painter.setRenderHint(
                    QPainter.RenderHint.Antialiasing
                )

                path = QPainterPath()

                path.addEllipse(
                    0,
                    0,
                    54,
                    54
                )

                painter.setClipPath(
                    path
                )

                painter.drawPixmap(
                    0,
                    0,
                    pixmap
                )

                painter.end()

                self.profile_photo.setPixmap(
                    circular_pixmap
                )

                return

        # ==================================================
        # FALLBACK
        # ==================================================

        self.profile_photo.setText(
            "👤"
        )

        self.profile_photo.setStyleSheet("""
            QLabel {
                background-color: #1b2430;
                border: 1px solid #394656;
                border-radius: 27px;
                font-size: 25px;
            }
        """)

    # ======================================================
    # CHATBOT TOGGLE
    # ======================================================

    def toggle_chatbot(self):

        if self.chatbot is None:

            self.chatbot = ChatbotPanel(
                self.username
            )

            self.chatbot.close_requested.connect(
                self.close_chatbot
            )

            self.chatbot.setParent(
                self
            )

            self.chatbot.show()

            self.position_chatbot()

            self.chatbot.raise_()

        else:

            if self.chatbot.isVisible():

                self.close_chatbot()

            else:

                self.chatbot.show()

                self.position_chatbot()

                self.chatbot.raise_()

    # ======================================================
    # CLOSE CHATBOT
    # ======================================================

    def close_chatbot(self):

        if self.chatbot:

            self.chatbot.hide()

    # ======================================================
    # POSITION CHATBOT PANEL
    # ======================================================

    def position_chatbot(self):

        if self.chatbot is None:
            return

        margin = 20

        panel_width = 340

        panel_height = max(
            300,
            self.height() - 40
        )

        self.chatbot.setGeometry(
            self.width() - panel_width - margin,
            margin,
            panel_width,
            panel_height
        )

        self.chatbot.raise_()

    # ======================================================
    # POSITION CHATBOT BUTTON
    # ======================================================

    def position_chatbot_button(self):

        if not hasattr(
            self,
            "chatbot_button"
        ):
            return

        margin_right = 25
        margin_bottom = 25

        x = (
            self.width()
            - self.chatbot_button.width()
            - margin_right
        )

        y = (
            self.height()
            - self.chatbot_button.height()
            - margin_bottom
        )

        self.chatbot_button.move(
            x,
            y
        )

        self.chatbot_button.raise_()

    # ======================================================
    # GESTURE CONTROL
    # ======================================================

    def start_gesture_control(self):

        if self.gesture_worker is not None:
            return

        self.gesture_status_label.setText(
            "GESTURE CONTROL • STARTING"
        )

        self.gesture_worker = DesktopGestureWorker()

        self.gesture_worker.gesture_detected.connect(
            self.handle_gesture
        )

        self.gesture_worker.camera_frame.connect(
            self.update_camera_preview
        )

        self.gesture_worker.error_occurred.connect(
            self.handle_gesture_error
        )

        self.gesture_worker.start()

    def stop_gesture_control(self):

        if self.gesture_worker is None:
            return

        worker = self.gesture_worker

        self.gesture_worker = None

        worker.stop()

        if self.camera_preview is not None:
            self.camera_preview.clear()
            self.camera_preview.setText(
                "CAMERA RESERVED\nFOR VISION STUDIO"
            )

        if self.gesture_status_label is not None:
            self.gesture_status_label.setText(
                "GESTURE CONTROL • PAUSED"
            )

    def start_camera_ownership_monitor(self):

        self.camera_ownership_timer = QTimer(self)

        self.camera_ownership_timer.timeout.connect(
            self.monitor_camera_ownership
        )

        self.camera_ownership_timer.start(300)

    def monitor_camera_ownership(self):

        # Vision Studio is the only FRIDAY child application
        # currently expected to use the physical camera.
        if self.vision_studio is not None:

            if self.vision_studio.isVisible():

                if self.gesture_worker is not None:
                    self.stop_gesture_control()

                return

            # Vision Studio was closed/hidden. Give the camera
            # back to the gesture engine.
            if (
                self.gesture_worker is None
                and not self.isHidden()
            ):
                self.start_gesture_control()

    def handle_gesture(self, gesture):

        if self.gesture_status_label is not None:
            self.gesture_status_label.setText(
                f"GESTURE CONTROL • {gesture.replace('_', ' ')}"
            )

        if gesture == "TWO_FINGER":
            self.toggle_chatbot()

        elif gesture == "OPEN_PALM":
            self.close_active_application()

        elif gesture == "FIST":
            self.close_active_application()

        elif gesture == "THUMBS_UP":
            self.activate_thumbs_up_command()

        elif gesture == "TWO_THUMBS_UP":
            self.take_screenshot()

    def activate_thumbs_up_command(self):
        phrase = "Hey Awesome!, Ready to shine? 1 2 3 Go!!!"

        if self.gesture_status_label is not None:
            self.gesture_status_label.setText(
                "GESTURE CONTROL • TYPING MESSAGE"
            )

        try:
            pyautogui.write(phrase, interval=0.06)
            self.open_media_controller()

            if self.gesture_status_label is not None:
                self.gesture_status_label.setText(
                    "GESTURE CONTROL • MESSAGE TYPED ✓"
                )
        except Exception as error:
            if self.gesture_status_label is not None:
                self.gesture_status_label.setText(
                    "GESTURE CONTROL • ACTION FAILED"
                )
            print("FRIDAY thumbs-up action error:", error)

    def take_screenshot(self):
        from datetime import datetime

        screenshot_directory = os.path.join("data", "screenshots")
        os.makedirs(screenshot_directory, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(
            screenshot_directory,
            f"FRIDAY_{timestamp}.png"
        )

        try:
            pyautogui.screenshot().save(screenshot_path)

            if self.gesture_status_label is not None:
                self.gesture_status_label.setText(
                    "GESTURE CONTROL • SCREENSHOT SAVED ✓"
                )

            print("FRIDAY screenshot saved:", screenshot_path)
        except Exception as error:
            if self.gesture_status_label is not None:
                self.gesture_status_label.setText(
                    "GESTURE CONTROL • SCREENSHOT FAILED"
                )
            print("FRIDAY screenshot error:", error)

    def update_camera_preview(self, frame):

        if self.camera_preview is None:
            return

        height, width, channels = frame.shape
        bytes_per_line = channels * width

        image = QImage(
            frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        ).copy()

        pixmap = QPixmap.fromImage(image)

        pixmap = pixmap.scaled(
            self.camera_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.camera_preview.setPixmap(pixmap)

    def handle_gesture_error(self, message):

        if self.gesture_status_label is not None:
            self.gesture_status_label.setText(
                "GESTURE CONTROL • CAMERA ERROR"
            )

        print("FRIDAY gesture error:", message)

    def close_active_application(self):

        windows = [
            self.system_panel,
            self.vision_studio,
            self.media_controller,
            self.tools,
            self.calendar
        ]

        for window in windows:
            if window is not None and window.isVisible():
                window.close()
                return

    # ======================================================
    # SYSTEM MONITOR
    # ======================================================

    def start_system_monitor(self):

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_system_stats
        )

        self.timer.start(
            1000
        )

        self.update_system_stats()

    def update_system_stats(self):

        cpu = psutil.cpu_percent()

        ram = psutil.virtual_memory().percent

        self.system_label.setText(
            f"CPU  {cpu:.0f}%     RAM  {ram:.0f}%"
        )

        current_time = QTime.currentTime()

        self.clock_label.setText(
            current_time.toString(
                "HH:mm"
            )
        )

    # ======================================================
    # APPLICATION WINDOWS
    # ======================================================

    def open_system_panel(self):

        if self.system_panel is None:

            self.system_panel = SystemPanel()

        self.system_panel.show()
        self.system_panel.raise_()
        self.system_panel.activateWindow()

    def open_vision_studio(self):

        # Vision Studio needs exclusive access to the webcam.
        # Release FRIDAY's gesture camera BEFORE creating it.
        self.stop_gesture_control()

        if self.vision_studio is None:

            self.vision_studio = VisionStudio()

        self.vision_studio.show()
        self.vision_studio.raise_()
        self.vision_studio.activateWindow()

    def open_media_controller(self):

        if self.media_controller is None:

            self.media_controller = MediaController()

        self.media_controller.show()
        self.media_controller.raise_()
        self.media_controller.activateWindow()

    def open_tools(self):

        if self.tools is None:

            self.tools = Tools()

        self.tools.show()
        self.tools.raise_()
        self.tools.activateWindow()

    def open_calendar(self):

        if self.calendar is None:

            self.calendar = Calendar()

        self.calendar.show()
        self.calendar.raise_()
        self.calendar.activateWindow()

    # ======================================================
    # RESIZE
    # ======================================================

    def resizeEvent(self, event):

        super().resizeEvent(
            event
        )

        self.position_chatbot_button()

        if (
            self.chatbot is not None
            and self.chatbot.isVisible()
        ):

            self.position_chatbot()

    # ======================================================
    # KEYBOARD
    # ======================================================

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

            super().keyPressEvent(
                event
            )

    # ======================================================
    # CLOSE
    # ======================================================

    def closeEvent(self, event):

        if self.camera_ownership_timer is not None:
            self.camera_ownership_timer.stop()

        if self.gesture_worker is not None:
            self.gesture_worker.stop()
            self.gesture_worker = None

        if hasattr(
            self,
            "timer"
        ):

            self.timer.stop()


        if self.system_panel:

            self.system_panel.close()

        if self.vision_studio:

            self.vision_studio.close()

        if self.media_controller:

            self.media_controller.close()

        if self.tools:

            self.tools.close()

        if self.calendar:

            self.calendar.close()

        if self.chatbot:

            self.chatbot.close()

        event.accept()