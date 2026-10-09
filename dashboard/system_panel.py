import sys
import os
import time
import psutil

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton
)
from dashboard.theme import apply_cloud_garden_theme


class SystemPanel(QWidget):
    return_home_requested = pyqtSignal()

    def __init__(self):

        super().__init__()

        self.setWindowTitle("FRIDAY — System")

        self.setMinimumSize(
            800,
            600
        )

        self.setup_ui()

        self.start_monitoring()

    # =========================================================
    # UI
    # =========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            30,
            25,
            30,
            25
        )

        main_layout.setSpacing(18)

        # -----------------------------------------------------
        # HEADER
        # -----------------------------------------------------

        header_layout = QHBoxLayout()

        title = QLabel(
            "SYSTEM"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                32,
                QFont.Weight.Bold
            )
        )

        subtitle = QLabel(
            "Live system monitoring"
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

        # -----------------------------------------------------
        # RESOURCE CARDS
        # -----------------------------------------------------

        cards_layout = QHBoxLayout()

        self.cpu_card = self.create_card(
            "CPU",
            "-- %"
        )

        self.ram_card = self.create_card(
            "RAM",
            "-- %"
        )

        self.disk_card = self.create_card(
            "DISK",
            "-- %"
        )

        self.battery_card = self.create_card(
            "BATTERY",
            "--"
        )

        cards_layout.addWidget(
            self.cpu_card
        )

        cards_layout.addWidget(
            self.ram_card
        )

        cards_layout.addWidget(
            self.disk_card
        )

        cards_layout.addWidget(
            self.battery_card
        )

        main_layout.addLayout(
            cards_layout
        )

        # -----------------------------------------------------
        # SYSTEM INFORMATION
        # -----------------------------------------------------

        details_frame = QFrame()

        details_frame.setObjectName(
            "detailsFrame"
        )

        details_layout = QVBoxLayout()

        details_layout.setContentsMargins(
            20,
            18,
            20,
            18
        )

        details_title = QLabel(
            "SYSTEM INFORMATION"
        )

        details_title.setFont(
            QFont(
                "Segoe UI",
                14,
                QFont.Weight.Bold
            )
        )

        self.processor_label = QLabel(
            "Processor: --"
        )

        self.memory_label = QLabel(
            "Memory: --"
        )

        self.uptime_label = QLabel(
            "Uptime: --"
        )

        details_layout.addWidget(
            details_title
        )

        details_layout.addSpacing(
            8
        )

        details_layout.addWidget(
            self.processor_label
        )

        details_layout.addWidget(
            self.memory_label
        )

        details_layout.addWidget(
            self.uptime_label
        )

        details_frame.setLayout(
            details_layout
        )

        main_layout.addWidget(
            details_frame
        )

        main_layout.addStretch()

        # -----------------------------------------------------
        # CLOSE BUTTON
        # -----------------------------------------------------

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setFixedHeight(
            58
        )

        close_button.clicked.connect(
            self.return_home_requested.emit
        )

        main_layout.addWidget(
            close_button
        )

        self.setLayout(
            main_layout
        )

        # -----------------------------------------------------
        # STYLE
        # -----------------------------------------------------

        apply_cloud_garden_theme(self, """
            QLabel#systemMetricTitle { font-size: 15pt; }
            QLabel#systemMetricValue { font-size: 34pt; font-weight: bold; }
        """)

    # =========================================================
    # CREATE RESOURCE CARD
    # =========================================================

    def create_card(
        self,
        title,
        value
    ):

        card = QFrame()

        card.setObjectName(
            "card"
        )

        layout = QVBoxLayout()

        layout.setContentsMargins(
            26,
            24,
            26,
            24
        )
        card.setMinimumHeight(190)

        title_label = QLabel(
            title
        )
        title_label.setObjectName("systemMetricTitle")

        title_label.setFont(
            QFont(
                "Segoe UI",
                15
            )
        )

        value_label = QLabel(
            value
        )
        value_label.setObjectName("systemMetricValue")

        value_label.setFont(
            QFont(
                "Segoe UI",
                34,
                QFont.Weight.Bold
            )
        )

        value_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            title_label
        )

        layout.addSpacing(
            8
        )

        layout.addWidget(
            value_label
        )

        card.setLayout(
            layout
        )

        card.value_label = value_label

        return card

    # =========================================================
    # MONITORING
    # =========================================================

    def start_monitoring(self):

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_system_info
        )

        self.timer.start(
            1000
        )

        self.update_system_info()

    # =========================================================
    # UPDATE SYSTEM INFORMATION
    # =========================================================

    def update_system_info(self):

        # -----------------------------------------------------
        # CPU
        # -----------------------------------------------------
        try:
            cpu = psutil.cpu_percent()
            self.cpu_card.value_label.setText(
                f"{cpu:.0f}%"
            )
        except Exception:
            self.cpu_card.value_label.setText("N/A")

        # -----------------------------------------------------
        # RAM
        # -----------------------------------------------------
        try:
            ram = psutil.virtual_memory()
            self.ram_card.value_label.setText(
                f"{ram.percent:.0f}%"
            )
        except Exception:
            ram = None
            self.ram_card.value_label.setText("N/A")

        # -----------------------------------------------------
        # DISK (Cross-platform root path: '/' on macOS/Linux, 'C:\\' on Windows)
        # -----------------------------------------------------
        try:
            disk_path = "/" if sys.platform != "win32" else "C:\\"
            disk = psutil.disk_usage(disk_path)
            self.disk_card.value_label.setText(
                f"{disk.percent:.0f}%"
            )
        except Exception:
            self.disk_card.value_label.setText("N/A")

        # -----------------------------------------------------
        # BATTERY
        # -----------------------------------------------------
        try:
            battery = psutil.sensors_battery()
            if battery is not None:
                self.battery_card.value_label.setText(
                    f"{battery.percent:.0f}%"
                )
            else:
                self.battery_card.value_label.setText(
                    "N/A"
                )
        except Exception:
            self.battery_card.value_label.setText("N/A")

        # -----------------------------------------------------
        # PROCESSOR
        # -----------------------------------------------------
        try:
            physical_cores = psutil.cpu_count(logical=False) or 0
            logical_cores = psutil.cpu_count(logical=True) or 0
            self.processor_label.setText(
                f"Processor: "
                f"{physical_cores} cores / "
                f"{logical_cores} logical processors"
            )
        except Exception:
            self.processor_label.setText("Processor: N/A")

        # -----------------------------------------------------
        # MEMORY
        # -----------------------------------------------------
        try:
            if ram is not None:
                total_memory = ram.total / (1024 ** 3)
                self.memory_label.setText(
                    f"Memory: "
                    f"{total_memory:.1f} GB"
                )
            else:
                self.memory_label.setText("Memory: N/A")
        except Exception:
            self.memory_label.setText("Memory: N/A")

        # -----------------------------------------------------
        # UPTIME
        # -----------------------------------------------------
        try:
            boot_time = psutil.boot_time()
            elapsed = time.time() - boot_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.uptime_label.setText(
                f"Uptime: "
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )
        except Exception:
            self.uptime_label.setText("Uptime: N/A")

    # =========================================================
    # KEYBOARD CONTROLS
    # =========================================================

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

    # =========================================================
    # CLOSE
    # =========================================================

    def closeEvent(self, event):

        if hasattr(
            self,
            "timer"
        ):

            self.timer.stop()

        event.accept()