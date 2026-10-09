from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame
)

from dashboard.theme import apply_cloud_garden_theme


class GestureLabPanel(QWidget):
    return_home_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("GESTURE LAB")
        title.setObjectName("gestureTitle")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("NO GESTURE")
        self.status_label.setObjectName("gestureName")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(180)
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        close_button = QPushButton("Back to Idle")
        close_button.setMinimumSize(240, 58)
        close_button.clicked.connect(self.return_home_requested.emit)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)

        apply_cloud_garden_theme(self, """
            QLabel#gestureTitle { color: #64856E; font-size: 16pt; font-weight: bold; }
            QLabel#gestureName { color: #376D68; font-family: Georgia; font-size: 44pt; font-weight: bold; }
        """)

    def set_gesture_name(self, gesture):
        self.status_label.setText(gesture.replace("_", " "))