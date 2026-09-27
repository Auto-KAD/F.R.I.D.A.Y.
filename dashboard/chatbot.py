from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit
)


class ChatbotPanel(QFrame):

    close_requested = pyqtSignal()

    def __init__(self, username):

        super().__init__()

        self.username = username

        self.setObjectName("chatbotPanel")

        self.setFixedWidth(340)

        self.setup_ui()

    def setup_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            20,
            18,
            20,
            18
        )

        main_layout.setSpacing(12)

        # ==================================================
        # HEADER
        # ==================================================

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title_layout.setSpacing(0)

        title = QLabel("FRIDAY")

        title.setFont(
            QFont(
                "Segoe UI",
                20,
                QFont.Weight.Bold
            )
        )

        subtitle = QLabel("AI ASSISTANT")

        subtitle.setFont(
            QFont(
                "Segoe UI",
                9
            )
        )

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        close_button = QPushButton("×")

        close_button.setFixedSize(
            32,
            32
        )

        close_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        close_button.clicked.connect(
            self.close_requested.emit
        )

        header_layout.addWidget(
            close_button
        )

        main_layout.addLayout(
            header_layout
        )

        # ==================================================
        # CHAT AREA
        # ==================================================

        self.chat_area = QTextEdit()

        self.chat_area.setReadOnly(True)

        self.chat_area.setText(
            f"FRIDAY: Hello, {self.username}.\n\n"
            "I am ready to assist you.\n"
            "Ask me something to begin."
        )

        main_layout.addWidget(
            self.chat_area,
            1
        )

        # ==================================================
        # INPUT AREA
        # ==================================================

        input_layout = QHBoxLayout()

        self.input_box = QLineEdit()

        self.input_box.setPlaceholderText(
            "Ask FRIDAY..."
        )

        self.input_box.returnPressed.connect(
            self.send_message
        )

        send_button = QPushButton("➤")

        send_button.setFixedSize(
            42,
            42
        )

        send_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        send_button.clicked.connect(
            self.send_message
        )

        input_layout.addWidget(
            self.input_box
        )

        input_layout.addWidget(
            send_button
        )

        main_layout.addLayout(
            input_layout
        )

        self.setLayout(
            main_layout
        )

        # ==================================================
        # STYLE
        # ==================================================

        self.setStyleSheet("""
            QFrame#chatbotPanel {
                background-color: #111720;
                border-left: 1px solid #303a48;
                border-top: 1px solid #303a48;
                border-bottom: 1px solid #303a48;
                border-top-left-radius: 18px;
                border-bottom-left-radius: 18px;
            }

            QLabel {
                color: #e8f0ff;
                background-color: transparent;
            }

            QTextEdit {
                background-color: #0b0f14;
                color: #e8f0ff;
                border: 1px solid #27313e;
                border-radius: 12px;
                padding: 10px;
                font-family: "Segoe UI";
                font-size: 11px;
            }

            QLineEdit {
                background-color: #0b0f14;
                color: #ffffff;
                border: 1px solid #394656;
                border-radius: 12px;
                padding: 10px;
                font-family: "Segoe UI";
                font-size: 11px;
            }

            QLineEdit:focus {
                border: 1px solid #6d8097;
            }

            QPushButton {
                background-color: #1b2430;
                color: #e8f0ff;
                border: 1px solid #323d4c;
                border-radius: 10px;
                font-family: "Segoe UI";
                font-size: 12px;
            }

            QPushButton:hover {
                background-color: #273342;
                border: 1px solid #566579;
            }

            QPushButton:pressed {
                background-color: #303d4d;
            }
        """)

    # ======================================================
    # SEND MESSAGE
    # ======================================================

    def send_message(self):

        message = self.input_box.text().strip()

        if not message:
            return

        self.chat_area.append(
            f"\nYOU: {message}"
        )

        self.chat_area.append(
            "\nFRIDAY: I received your message."
        )

        self.input_box.clear()

        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )