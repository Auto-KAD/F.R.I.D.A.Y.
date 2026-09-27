import pyautogui

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame
)


class MediaController(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "FRIDAY — Media Controller"
        )

        self.setMinimumSize(
            800,
            600
        )

        self.is_playing = False
        self.is_muted = False

        self.setup_ui()

    # --------------------------------------------------
    # USER INTERFACE
    # --------------------------------------------------

    def setup_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            35,
            30,
            35,
            30
        )

        main_layout.setSpacing(
            20
        )

        # ----------------------------------------------
        # HEADER
        # ----------------------------------------------

        header_layout = QHBoxLayout()

        title = QLabel(
            "MEDIA CONTROLLER"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                28,
                QFont.Weight.Bold
            )
        )

        subtitle = QLabel(
            "System media control"
        )

        subtitle.setFont(
            QFont(
                "Segoe UI",
                13
            )
        )

        header_layout.addWidget(
            title
        )

        header_layout.addSpacing(
            20
        )

        header_layout.addWidget(
            subtitle
        )

        header_layout.addStretch()

        main_layout.addLayout(
            header_layout
        )

        # ----------------------------------------------
        # NOW PLAYING CARD
        # ----------------------------------------------

        media_frame = QFrame()

        media_frame.setObjectName(
            "mediaFrame"
        )

        media_layout = QVBoxLayout()

        media_layout.setContentsMargins(
            30,
            25,
            30,
            25
        )

        media_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # MUSIC ICON

        icon = QLabel(
            "♫"
        )

        icon.setFont(
            QFont(
                "Segoe UI Symbol",
                58,
                QFont.Weight.Normal
            )
        )

        icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon.setMinimumHeight(
            75
        )

        # MEDIA TITLE

        self.media_title = QLabel(
            "NO MEDIA DETECTED"
        )

        self.media_title.setFont(
            QFont(
                "Segoe UI",
                22,
                QFont.Weight.Bold
            )
        )

        self.media_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # MEDIA STATUS

        self.media_status = QLabel(
            "Ready"
        )

        self.media_status.setFont(
            QFont(
                "Segoe UI",
                14
            )
        )

        self.media_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        media_layout.addWidget(
            icon
        )

        media_layout.addSpacing(
            5
        )

        media_layout.addWidget(
            self.media_title
        )

        media_layout.addSpacing(
            8
        )

        media_layout.addWidget(
            self.media_status
        )

        media_frame.setLayout(
            media_layout
        )

        main_layout.addWidget(
            media_frame
        )

        # ----------------------------------------------
        # MAIN MEDIA CONTROLS
        # ----------------------------------------------

        controls_frame = QFrame()

        controls_frame.setObjectName(
            "controlsFrame"
        )

        controls_layout = QHBoxLayout()

        controls_layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        controls_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # PREVIOUS

        previous_button = self.create_button(
            "◀",
            65,
            25
        )

        # PLAY

        self.play_button = self.create_button(
            "▶",
            78,
            30
        )

        # NEXT

        next_button = self.create_button(
            "▶",
            65,
            25
        )

        # Add a small next-track indicator

        next_button.setText(
            "▶|"
        )

        previous_button.setText(
            "|◀"
        )

        previous_button.clicked.connect(
            self.previous_media
        )

        self.play_button.clicked.connect(
            self.toggle_play_pause
        )

        next_button.clicked.connect(
            self.next_media
        )

        controls_layout.addWidget(
            previous_button
        )

        controls_layout.addSpacing(
            18
        )

        controls_layout.addWidget(
            self.play_button
        )

        controls_layout.addSpacing(
            18
        )

        controls_layout.addWidget(
            next_button
        )

        controls_frame.setLayout(
            controls_layout
        )

        main_layout.addWidget(
            controls_frame
        )

        # ----------------------------------------------
        # VOLUME CONTROLS
        # ----------------------------------------------

        volume_frame = QFrame()

        volume_frame.setObjectName(
            "volumeFrame"
        )

        volume_layout = QHBoxLayout()

        volume_layout.setContentsMargins(
            25,
            18,
            25,
            18
        )

        volume_title = QLabel(
            "VOLUME"
        )

        volume_title.setFont(
            QFont(
                "Segoe UI",
                14,
                QFont.Weight.Bold
            )
        )

        volume_down = self.create_button(
            "−",
            58,
            24
        )

        self.mute_button = self.create_button(
            "MUTE",
            75,
            13
        )

        volume_up = self.create_button(
            "+",
            58,
            24
        )

        volume_down.clicked.connect(
            self.volume_down
        )

        volume_up.clicked.connect(
            self.volume_up
        )

        self.mute_button.clicked.connect(
            self.toggle_mute
        )

        volume_layout.addWidget(
            volume_title
        )

        volume_layout.addStretch()

        volume_layout.addWidget(
            volume_down
        )

        volume_layout.addSpacing(
            12
        )

        volume_layout.addWidget(
            self.mute_button
        )

        volume_layout.addSpacing(
            12
        )

        volume_layout.addWidget(
            volume_up
        )

        volume_frame.setLayout(
            volume_layout
        )

        main_layout.addWidget(
            volume_frame
        )

        # ----------------------------------------------
        # STATUS
        # ----------------------------------------------

        self.status_label = QLabel(
            "STATUS: READY"
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setFont(
            QFont(
                "Segoe UI",
                13
            )
        )

        main_layout.addWidget(
            self.status_label
        )

        main_layout.addStretch()

        # ----------------------------------------------
        # CLOSE BUTTON
        # ----------------------------------------------

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setFixedHeight(
            45
        )

        close_button.setFont(
            QFont(
                "Segoe UI",
                12
            )
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

        # ----------------------------------------------
        # STYLE
        # ----------------------------------------------

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f14;
                color: #e8f0ff;
            }

            QLabel {
                background-color: transparent;
                color: #e8f0ff;
            }

            QFrame#mediaFrame {
                background-color: #111720;
                border: 1px solid #303a48;
                border-radius: 18px;
            }

            QFrame#controlsFrame {
                background-color: #141b24;
                border: 1px solid #303a48;
                border-radius: 16px;
            }

            QFrame#volumeFrame {
                background-color: #111720;
                border: 1px solid #27313e;
                border-radius: 14px;
            }

            QPushButton {
                background-color: #1b2430;
                color: #e8f0ff;
                border: 1px solid #3a4657;
                border-radius: 12px;
                font-family: "Segoe UI";
                padding: 5px;
            }

            QPushButton:hover {
                background-color: #273342;
                border: 1px solid #65758a;
            }

            QPushButton:pressed {
                background-color: #303d4d;
            }
        """)

    # --------------------------------------------------
    # BUTTON CREATION
    # --------------------------------------------------

    def create_button(
        self,
        text,
        size,
        font_size
    ):

        button = QPushButton(
            text
        )

        button.setFixedSize(
            size,
            size
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.setFont(
            QFont(
                "Segoe UI Symbol",
                font_size,
                QFont.Weight.Bold
            )
        )

        return button

    # --------------------------------------------------
    # MEDIA ACTIONS
    # --------------------------------------------------

    def toggle_play_pause(self):

        pyautogui.press(
            "playpause"
        )

        self.is_playing = not self.is_playing

        if self.is_playing:

            self.play_button.setText(
                "Ⅱ"
            )

            self.media_status.setText(
                "Playing"
            )

            self.status_label.setText(
                "STATUS: MEDIA PLAYING"
            )

        else:

            self.play_button.setText(
                "▶"
            )

            self.media_status.setText(
                "Paused"
            )

            self.status_label.setText(
                "STATUS: MEDIA PAUSED"
            )

    def next_media(self):

        pyautogui.press(
            "nexttrack"
        )

        self.media_status.setText(
            "Next track"
        )

        self.status_label.setText(
            "STATUS: NEXT TRACK"
        )

    def previous_media(self):

        pyautogui.press(
            "prevtrack"
        )

        self.media_status.setText(
            "Previous track"
        )

        self.status_label.setText(
            "STATUS: PREVIOUS TRACK"
        )

    # --------------------------------------------------
    # VOLUME
    # --------------------------------------------------

    def volume_up(self):

        pyautogui.press(
            "volumeup"
        )

        self.status_label.setText(
            "STATUS: VOLUME UP"
        )

        self.media_status.setText(
            "Volume increased"
        )

    def volume_down(self):

        pyautogui.press(
            "volumedown"
        )

        self.status_label.setText(
            "STATUS: VOLUME DOWN"
        )

        self.media_status.setText(
            "Volume decreased"
        )

    def toggle_mute(self):

        pyautogui.press(
            "volumemute"
        )

        self.is_muted = not self.is_muted

        if self.is_muted:

            self.mute_button.setText(
                "UNMUTE"
            )

            self.media_status.setText(
                "Muted"
            )

            self.status_label.setText(
                "STATUS: MUTED"
            )

        else:

            self.mute_button.setText(
                "MUTE"
            )

            self.media_status.setText(
                "Audio restored"
            )

            self.status_label.setText(
                "STATUS: AUDIO ACTIVE"
            )

    # --------------------------------------------------
    # FULLSCREEN
    # --------------------------------------------------

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