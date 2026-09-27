import cv2
import math
import time

from PyQt6.QtCore import (
    Qt,
    QTimer
)

from PyQt6.QtGui import (
    QFont,
    QImage,
    QPixmap
)

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QLineEdit,
    QComboBox,
    QTabWidget,
    QMessageBox
)

from vision.camera import Camera


class Tools(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "FRIDAY — Quick Tools"
        )

        self.setMinimumSize(
            900,
            650
        )

        # --------------------------------
        # TIMER
        # --------------------------------

        self.timer_seconds = 0

        self.timer_running = False

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_timer
        )

        # --------------------------------
        # STOPWATCH
        # --------------------------------

        self.stopwatch_running = False

        self.stopwatch_start_time = 0

        self.stopwatch_elapsed = 0

        self.stopwatch_timer = QTimer()

        self.stopwatch_timer.timeout.connect(
            self.update_stopwatch
        )

        # --------------------------------
        # QR CAMERA
        # --------------------------------

        self.qr_camera = None

        self.qr_timer = None

        self.qr_detector = cv2.QRCodeDetector()

        self.setup_ui()

    # ==================================================
    # MAIN UI
    # ==================================================

    def setup_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            30,
            25,
            30,
            25
        )

        main_layout.setSpacing(
            18
        )

        # --------------------------------
        # HEADER
        # --------------------------------

        header_layout = QHBoxLayout()

        title = QLabel(
            "QUICK TOOLS"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                28,
                QFont.Weight.Bold
            )
        )

        subtitle = QLabel(
            "FRIDAY utility center"
        )

        subtitle.setFont(
            QFont(
                "Segoe UI",
                12
            )
        )

        header_layout.addWidget(
            title
        )

        header_layout.addSpacing(
            18
        )

        header_layout.addWidget(
            subtitle
        )

        header_layout.addStretch()

        main_layout.addLayout(
            header_layout
        )

        # --------------------------------
        # TABS
        # --------------------------------

        self.tabs = QTabWidget()

        self.tabs.addTab(
            self.create_calculator(),
            "CALCULATOR"
        )

        self.tabs.addTab(
            self.create_unit_converter(),
            "UNIT CONVERTER"
        )

        self.tabs.addTab(
            self.create_timer(),
            "TIMER"
        )

        self.tabs.addTab(
            self.create_stopwatch(),
            "STOPWATCH"
        )

        self.tabs.addTab(
            self.create_qr_generator(),
            "QR GENERATOR"
        )

        self.tabs.addTab(
            self.create_qr_scanner(),
            "QR SCANNER"
        )

        main_layout.addWidget(
            self.tabs,
            1
        )

        # --------------------------------
        # CLOSE
        # --------------------------------

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setFixedHeight(
            42
        )

        close_button.clicked.connect(
            self.close
        )

        main_layout.addWidget(
            close_button
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

            QLabel {
                background-color: transparent;
                color: #e8f0ff;
            }

            QTabWidget::pane {
                border: 1px solid #303a48;
                border-radius: 14px;
                background-color: #111720;
            }

            QTabBar::tab {
                background-color: #141b24;
                color: #aeb9c8;
                border: 1px solid #303a48;
                padding: 10px 16px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-family: "Segoe UI";
                font-size: 11px;
            }

            QTabBar::tab:selected {
                background-color: #273342;
                color: #ffffff;
                border-bottom: 2px solid #8fa8c7;
            }

            QTabBar::tab:hover {
                background-color: #202b39;
            }

            QFrame#toolFrame {
                background-color: #141b24;
                border: 1px solid #303a48;
                border-radius: 14px;
            }

            QLineEdit {
                background-color: #0f151d;
                color: #ffffff;
                border: 1px solid #394656;
                border-radius: 9px;
                padding: 9px;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #6d8097;
            }

            QComboBox {
                background-color: #1b2430;
                color: #ffffff;
                border: 1px solid #394656;
                border-radius: 9px;
                padding: 9px;
            }

            QPushButton {
                background-color: #1b2430;
                color: #e8f0ff;
                border: 1px solid #323d4c;
                border-radius: 10px;
                font-family: "Segoe UI";
                font-size: 12px;
                padding: 8px;
            }

            QPushButton:hover {
                background-color: #273342;
                border: 1px solid #566579;
            }

            QPushButton:pressed {
                background-color: #303d4d;
            }
        """)

    # ==================================================
    # CALCULATOR
    # ==================================================

    def create_calculator(self):

        widget = QWidget()

        layout = QVBoxLayout()

        layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        self.calculator_display = QLineEdit()

        self.calculator_display.setPlaceholderText(
            "Enter calculation..."
        )

        self.calculator_display.setFixedHeight(
            55
        )

        self.calculator_display.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        self.calculator_display.setFont(
            QFont(
                "Segoe UI",
                20
            )
        )

        layout.addWidget(
            self.calculator_display
        )

        grid = QGridLayout()

        buttons = [
            ("7", 0, 0),
            ("8", 0, 1),
            ("9", 0, 2),
            ("/", 0, 3),

            ("4", 1, 0),
            ("5", 1, 1),
            ("6", 1, 2),
            ("*", 1, 3),

            ("1", 2, 0),
            ("2", 2, 1),
            ("3", 2, 2),
            ("-", 2, 3),

            ("0", 3, 0),
            (".", 3, 1),
            ("C", 3, 2),
            ("+", 3, 3)
        ]

        for text, row, column in buttons:

            button = QPushButton(
                text
            )

            button.setMinimumHeight(
                55
            )

            button.clicked.connect(
                lambda checked=False,
                value=text:
                self.calculator_input(value)
            )

            grid.addWidget(
                button,
                row,
                column
            )

        equals_button = QPushButton(
            "="
        )

        equals_button.setMinimumHeight(
            55
        )

        equals_button.clicked.connect(
            self.calculate
        )

        grid.addWidget(
            equals_button,
            4,
            0,
            1,
            4
        )

        layout.addLayout(
            grid
        )

        widget.setLayout(
            layout
        )

        return widget

    def calculator_input(
        self,
        value
    ):

        if value == "C":

            self.calculator_display.clear()

            return

        current = (
            self.calculator_display.text()
        )

        self.calculator_display.setText(
            current + value
        )

    def calculate(self):

        expression = (
            self.calculator_display.text()
        )

        try:

            # Only allow calculator characters.
            allowed = (
                "0123456789+-*/(). "
            )

            if any(
                character not in allowed
                for character in expression
            ):

                raise ValueError

            result = eval(
                expression,
                {
                    "__builtins__": None
                },
                {}
            )

            self.calculator_display.setText(
                str(result)
            )

        except Exception:

            self.calculator_display.setText(
                "ERROR"
            )

    # ==================================================
    # UNIT CONVERTER
    # ==================================================

    def create_unit_converter(self):

        widget = QWidget()

        layout = QVBoxLayout()

        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        title = QLabel(
            "UNIT CONVERTER"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Weight.Bold
            )
        )

        layout.addWidget(
            title
        )

        self.unit_input = QLineEdit()

        self.unit_input.setPlaceholderText(
            "Enter value"
        )

        layout.addWidget(
            self.unit_input
        )

        self.unit_type = QComboBox()

        self.unit_type.addItems([
            "Kilometers → Miles",
            "Miles → Kilometers",
            "Meters → Feet",
            "Feet → Meters",
            "Kilograms → Pounds",
            "Pounds → Kilograms",
            "Celsius → Fahrenheit",
            "Fahrenheit → Celsius",
            "Liters → Gallons",
            "Gallons → Liters"
        ])

        layout.addWidget(
            self.unit_type
        )

        convert_button = QPushButton(
            "CONVERT"
        )

        convert_button.setFixedHeight(
            45
        )

        convert_button.clicked.connect(
            self.convert_units
        )

        layout.addWidget(
            convert_button
        )

        self.unit_result = QLabel(
            "Result: --"
        )

        self.unit_result.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Weight.Bold
            )
        )

        self.unit_result.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.unit_result
        )

        layout.addStretch()

        widget.setLayout(
            layout
        )

        return widget

    def convert_units(self):

        try:

            value = float(
                self.unit_input.text()
            )

            conversion = (
                self.unit_type.currentText()
            )

            if conversion == "Kilometers → Miles":

                result = value * 0.621371

            elif conversion == "Miles → Kilometers":

                result = value * 1.60934

            elif conversion == "Meters → Feet":

                result = value * 3.28084

            elif conversion == "Feet → Meters":

                result = value * 0.3048

            elif conversion == "Kilograms → Pounds":

                result = value * 2.20462

            elif conversion == "Pounds → Kilograms":

                result = value * 0.453592

            elif conversion == "Celsius → Fahrenheit":

                result = (
                    value * 9 / 5
                ) + 32

            elif conversion == "Fahrenheit → Celsius":

                result = (
                    value - 32
                ) * 5 / 9

            elif conversion == "Liters → Gallons":

                result = value * 0.264172

            elif conversion == "Gallons → Liters":

                result = value * 3.78541

            else:

                return

            self.unit_result.setText(
                f"Result: {result:.4f}"
            )

        except ValueError:

            self.unit_result.setText(
                "Result: Invalid value"
            )

    # ==================================================
    # TIMER
    # ==================================================

    def create_timer(self):

        widget = QWidget()

        layout = QVBoxLayout()

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title = QLabel(
            "TIMER"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                20,
                QFont.Weight.Bold
            )
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            title
        )

        self.timer_display = QLabel(
            "00:00:00"
        )

        self.timer_display.setFont(
            QFont(
                "Segoe UI",
                42,
                QFont.Weight.Bold
            )
        )

        self.timer_display.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.timer_display
        )

        input_layout = QHBoxLayout()

        self.timer_minutes = QLineEdit()

        self.timer_minutes.setPlaceholderText(
            "Minutes"
        )

        self.timer_minutes.setFixedWidth(
            130
        )

        self.timer_seconds_input = QLineEdit()

        self.timer_seconds_input.setPlaceholderText(
            "Seconds"
        )

        self.timer_seconds_input.setFixedWidth(
            130
        )

        input_layout.addWidget(
            self.timer_minutes
        )

        input_layout.addWidget(
            self.timer_seconds_input
        )

        layout.addLayout(
            input_layout
        )

        button_layout = QHBoxLayout()

        start_button = QPushButton(
            "START"
        )

        pause_button = QPushButton(
            "PAUSE"
        )

        reset_button = QPushButton(
            "RESET"
        )

        start_button.clicked.connect(
            self.start_timer
        )

        pause_button.clicked.connect(
            self.pause_timer
        )

        reset_button.clicked.connect(
            self.reset_timer
        )

        button_layout.addWidget(
            start_button
        )

        button_layout.addWidget(
            pause_button
        )

        button_layout.addWidget(
            reset_button
        )

        layout.addLayout(
            button_layout
        )

        layout.addStretch()

        widget.setLayout(
            layout
        )

        return widget

    def start_timer(self):

        if not self.timer_running:

            if self.timer_seconds <= 0:

                try:

                    minutes = int(
                        self.timer_minutes.text()
                        or 0
                    )

                    seconds = int(
                        self.timer_seconds_input.text()
                        or 0
                    )

                    self.timer_seconds = (
                        minutes * 60
                    ) + seconds

                except ValueError:

                    return

            if self.timer_seconds <= 0:

                return

            self.timer_running = True

            self.timer.start(
                1000
            )

    def pause_timer(self):

        self.timer_running = False

        self.timer.stop()

    def reset_timer(self):

        self.timer_running = False

        self.timer.stop()

        self.timer_seconds = 0

        self.timer_display.setText(
            "00:00:00"
        )

    def update_timer(self):

        if self.timer_seconds <= 0:

            self.timer.stop()

            self.timer_running = False

            self.timer_display.setText(
                "00:00:00"
            )

            QMessageBox.information(
                self,
                "FRIDAY Timer",
                "Timer completed."
            )

            return

        self.timer_seconds -= 1

        hours = (
            self.timer_seconds // 3600
        )

        minutes = (
            self.timer_seconds % 3600
        ) // 60

        seconds = (
            self.timer_seconds % 60
        )

        self.timer_display.setText(
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    # ==================================================
    # STOPWATCH
    # ==================================================

    def create_stopwatch(self):

        widget = QWidget()

        layout = QVBoxLayout()

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title = QLabel(
            "STOPWATCH"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                20,
                QFont.Weight.Bold
            )
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            title
        )

        self.stopwatch_display = QLabel(
            "00:00:00.00"
        )

        self.stopwatch_display.setFont(
            QFont(
                "Segoe UI",
                40,
                QFont.Weight.Bold
            )
        )

        self.stopwatch_display.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.stopwatch_display
        )

        buttons_layout = QHBoxLayout()

        start_button = QPushButton(
            "START"
        )

        stop_button = QPushButton(
            "STOP"
        )

        reset_button = QPushButton(
            "RESET"
        )

        start_button.clicked.connect(
            self.start_stopwatch
        )

        stop_button.clicked.connect(
            self.stop_stopwatch
        )

        reset_button.clicked.connect(
            self.reset_stopwatch
        )

        buttons_layout.addWidget(
            start_button
        )

        buttons_layout.addWidget(
            stop_button
        )

        buttons_layout.addWidget(
            reset_button
        )

        layout.addLayout(
            buttons_layout
        )

        layout.addStretch()

        widget.setLayout(
            layout
        )

        return widget

    def start_stopwatch(self):

        if self.stopwatch_running:

            return

        self.stopwatch_start_time = (
            time.perf_counter()
            - self.stopwatch_elapsed
        )

        self.stopwatch_running = True

        self.stopwatch_timer.start(
            10
        )

    def stop_stopwatch(self):

        if not self.stopwatch_running:

            return

        self.stopwatch_elapsed = (
            time.perf_counter()
            - self.stopwatch_start_time
        )

        self.stopwatch_running = False

        self.stopwatch_timer.stop()

    def reset_stopwatch(self):

        self.stopwatch_running = False

        self.stopwatch_timer.stop()

        self.stopwatch_elapsed = 0

        self.stopwatch_display.setText(
            "00:00:00.00"
        )

    def update_stopwatch(self):

        elapsed = (
            time.perf_counter()
            - self.stopwatch_start_time
        )

        self.stopwatch_elapsed = elapsed

        hours = int(
            elapsed // 3600
        )

        minutes = int(
            elapsed % 3600 // 60
        )

        seconds = int(
            elapsed % 60
        )

        milliseconds = int(
            (elapsed * 100) % 100
        )

        self.stopwatch_display.setText(
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}."
            f"{milliseconds:02d}"
        )

    # ==================================================
    # QR GENERATOR
    # ==================================================

    def create_qr_generator(self):

        widget = QWidget()

        layout = QVBoxLayout()

        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        title = QLabel(
            "QR GENERATOR"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Weight.Bold
            )
        )

        layout.addWidget(
            title
        )

        self.qr_input = QLineEdit()

        self.qr_input.setPlaceholderText(
            "Enter text, URL, contact information..."
        )

        self.qr_input.setFixedHeight(
            50
        )

        layout.addWidget(
            self.qr_input
        )

        generate_button = QPushButton(
            "GENERATE QR"
        )

        generate_button.setFixedHeight(
            45
        )

        generate_button.clicked.connect(
            self.generate_qr
        )

        layout.addWidget(
            generate_button
        )

        self.qr_image_label = QLabel(
            "QR CODE"
        )

        self.qr_image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.qr_image_label.setMinimumHeight(
            300
        )

        layout.addWidget(
            self.qr_image_label
        )

        layout.addStretch()

        widget.setLayout(
            layout
        )

        return widget

    def generate_qr(self):

        text = self.qr_input.text()

        if not text:

            return

        try:

            import qrcode

            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=4
            )

            qr.add_data(
                text
            )

            qr.make(
                fit=True
            )

            image = qr.make_image(
                fill_color="black",
                back_color="white"
            )

            filename = (
                "friday_qr_"
                + str(
                    int(
                        time.time()
                    )
                )
                + ".png"
            )

            image.save(
                filename
            )

            pixmap = QPixmap(
                filename
            )

            pixmap = pixmap.scaled(
                280,
                280,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.qr_image_label.setPixmap(
                pixmap
            )

        except Exception as error:

            self.qr_image_label.setText(
                f"QR generation error:\n{error}"
            )

    # ==================================================
    # QR SCANNER
    # ==================================================

    def create_qr_scanner(self):

        widget = QWidget()

        layout = QVBoxLayout()

        layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        title = QLabel(
            "QR SCANNER"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Weight.Bold
            )
        )

        layout.addWidget(
            title
        )

        self.qr_camera_label = QLabel(
            "Camera stopped"
        )

        self.qr_camera_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.qr_camera_label.setMinimumSize(
            600,
            350
        )

        self.qr_camera_label.setStyleSheet("""
            QLabel {
                background-color: #05080c;
                border: 1px solid #303a48;
                border-radius: 14px;
                color: #8f9baa;
            }
        """)

        layout.addWidget(
            self.qr_camera_label
        )

        self.qr_result = QLabel(
            "SCAN RESULT: --"
        )

        self.qr_result.setFont(
            QFont(
                "Segoe UI",
                13,
                QFont.Weight.Bold
            )
        )

        self.qr_result.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.qr_result
        )

        buttons_layout = QHBoxLayout()

        start_button = QPushButton(
            "START CAMERA"
        )

        stop_button = QPushButton(
            "STOP CAMERA"
        )

        start_button.clicked.connect(
            self.start_qr_camera
        )

        stop_button.clicked.connect(
            self.stop_qr_camera
        )

        buttons_layout.addWidget(
            start_button
        )

        buttons_layout.addWidget(
            stop_button
        )

        layout.addLayout(
            buttons_layout
        )

        widget.setLayout(
            layout
        )

        return widget

    def start_qr_camera(self):

        if self.qr_camera is not None:

            return

        try:

            self.qr_camera = Camera()

        except Exception as error:

            self.qr_camera_label.setText(
                f"Camera error:\n{error}"
            )

            return

        self.qr_timer = QTimer()

        self.qr_timer.timeout.connect(
            self.process_qr_frame
        )

        self.qr_timer.start(
            30
        )

    def process_qr_frame(self):

        if self.qr_camera is None:

            return

        frame = self.qr_camera.read()

        if frame is None:

            return

        data, points, _ = (
            self.qr_detector.detectAndDecode(
                frame
            )
        )

        if points is not None:

            points = points.astype(
                int
            )

            for i in range(
                len(points[0])
            ):

                start = tuple(
                    points[0][i]
                )

                end = tuple(
                    points[0][
                        (i + 1)
                        % len(points[0])
                    ]
                )

                cv2.line(
                    frame,
                    start,
                    end,
                    (0, 255, 0),
                    3
                )

        if data:

            self.qr_result.setText(
                f"SCAN RESULT: {data}"
            )

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

        image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )

        pixmap = QPixmap.fromImage(
            image
        )

        pixmap = pixmap.scaled(
            self.qr_camera_label.width(),
            self.qr_camera_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.qr_camera_label.setPixmap(
            pixmap
        )

    def stop_qr_camera(self):

        if self.qr_timer is not None:

            self.qr_timer.stop()

            self.qr_timer = None

        if self.qr_camera is not None:

            self.qr_camera.release()

            self.qr_camera = None

        self.qr_camera_label.clear()

        self.qr_camera_label.setText(
            "Camera stopped"
        )

    # ==================================================
    # CLOSE
    # ==================================================

    def closeEvent(
        self,
        event
    ):

        self.timer.stop()

        self.stopwatch_timer.stop()

        self.stop_qr_camera()

        event.accept()