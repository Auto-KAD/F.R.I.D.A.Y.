from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from dashboard.theme import apply_cloud_garden_theme


class JarvisPanel(QWidget):
    return_home_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("jarvisPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("J.A.R.V.I.S.")
        title.setFont(QFont("Georgia", 30, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("PERSONAL ASSISTANT")
        subtitle.setObjectName("eyebrow")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        status = QLabel("Assistant workspace ready")
        status.setObjectName("mutedText")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status)

        apply_cloud_garden_theme(self, """
            QWidget#jarvisPanel { background-color: rgba(255, 253, 246, 238); border: 1px solid #D7E2D8; border-radius: 14px; }
            QLabel#eyebrow { color: #64856E; font-weight: bold; }
            QLabel#mutedText { color: #71877A; }
        """)