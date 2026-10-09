import pyautogui
import os

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QFileDialog,
    QListWidget,
    QSlider
)
from dashboard.theme import apply_cloud_garden_theme


class MediaController(QWidget):
    return_home_requested = pyqtSignal()

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "FRIDAY — Media Controller"
        )

        self.setMinimumSize(
            900,
            650
        )

        self.is_playing = False
        self.is_muted = False
        self.playlist = []
        self.current_index = -1
        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.7)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.playbackStateChanged.connect(
            self.update_playback_state
        )
        self.media_player.mediaStatusChanged.connect(
            self.update_media_status
        )
        self.media_player.durationChanged.connect(
            self.update_duration
        )
        self.media_player.positionChanged.connect(
            self.update_position
        )
        self.media_player.errorOccurred.connect(
            self.handle_player_error
        )

        self.setup_ui()

    # --------------------------------------------------
    # USER INTERFACE
    # --------------------------------------------------

    def setup_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            24,
            20,
            24,
            20
        )

        main_layout.setSpacing(
            12
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
            "Your local playlist and system audio"
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

        self.open_button = QPushButton("＋  Add audio")
        self.open_button.setMinimumSize(180, 50)
        self.open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_button.clicked.connect(self.open_audio_files)
        header_layout.addWidget(self.open_button)

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
            "Choose a track or control system audio"
        )

        self.media_title.setWordWrap(True)

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

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderMoved.connect(
            self.media_player.setPosition
        )
        media_layout.addWidget(self.seek_slider)

        self.track_position_label = QLabel("00:00 / 00:00")
        self.track_position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_layout.addWidget(self.track_position_label)

        media_frame.setLayout(
            media_layout
        )

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        content_layout.addWidget(media_frame, 3)

        playlist_frame = QFrame()
        playlist_frame.setObjectName("playlistFrame")
        playlist_layout = QVBoxLayout(playlist_frame)
        playlist_layout.setContentsMargins(16, 14, 16, 14)
        playlist_title = QLabel("PLAY QUEUE")
        playlist_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        playlist_layout.addWidget(playlist_title)
        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(
            self.play_selected_track
        )
        playlist_layout.addWidget(self.playlist_widget, 1)
        content_layout.addWidget(playlist_frame, 2)
        main_layout.addLayout(content_layout, 1)

        # ----------------------------------------------
        # MAIN MEDIA CONTROLS
        # ----------------------------------------------

        controls_frame = QFrame()

        controls_frame.setObjectName(
            "controlsFrame"
        )

        controls_layout = QHBoxLayout()

        controls_layout.setContentsMargins(14, 12, 14, 12)

        controls_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # PREVIOUS

        previous_button = self.create_button(
            "◀",
            76,
            28
        )

        # PLAY

        self.play_button = self.create_button(
            "▶",
            92,
            34
        )

        # NEXT

        next_button = self.create_button(
            "▶",
            76,
            28
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
        controls_row = QHBoxLayout()
        controls_row.setSpacing(12)
        controls_row.addWidget(controls_frame, 1)

        # ----------------------------------------------
        # VOLUME CONTROLS
        # ----------------------------------------------

        volume_frame = QFrame()

        volume_frame.setObjectName(
            "volumeFrame"
        )

        volume_layout = QHBoxLayout()

        volume_layout.setContentsMargins(14, 10, 14, 10)

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
            66,
            26
        )

        self.mute_button = self.create_button(
            "MUTE",
            75,
            13
        )

        volume_up = self.create_button(
            "+",
            66,
            26
        )

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMinimumWidth(120)
        self.volume_slider.valueChanged.connect(
            self.set_player_volume
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
            self.volume_slider
        )

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
        controls_row.addWidget(volume_frame, 1)
        main_layout.addLayout(controls_row)

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
            self.return_home_requested.emit
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
        apply_cloud_garden_theme(self, """
            QFrame#mediaFrame, QFrame#controlsFrame, QFrame#volumeFrame { background-color: rgba(255, 253, 246, 238); }
            QListWidget { min-height: 110px; }
            QSlider::groove:horizontal { height: 8px; background: #D8E5D8; border-radius: 4px; }
            QSlider::handle:horizontal { background: #75A78A; width: 20px; margin: -7px 0; border-radius: 10px; }
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

    def open_audio_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add audio to FRIDAY",
            "",
            "Audio files (*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.wma);;All files (*)"
        )

        if not paths:
            return

        for path in paths:
            if path not in self.playlist:
                self.playlist.append(path)
                self.playlist_widget.addItem(os.path.basename(path))

        self.play_track(self.playlist.index(paths[0]))

    def play_selected_track(self, item=None):
        row = self.playlist_widget.row(item) if item is not None else self.playlist_widget.currentRow()
        if row >= 0:
            self.play_track(row)

    def play_track(self, index):
        if not 0 <= index < len(self.playlist):
            return

        self.current_index = index
        self.playlist_widget.setCurrentRow(index)
        track_path = self.playlist[index]
        self.media_title.setText(os.path.basename(track_path))
        self.media_status.setText("Loading audio…")
        self.status_label.setText("STATUS: LOADING TRACK")
        self.media_player.setSource(QUrl.fromLocalFile(track_path))
        self.media_player.play()

    def toggle_play_pause(self):
        if self.current_index >= 0:
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
            else:
                self.media_player.play()
        else:
            self.send_system_media_key("playpause", "play/pause")

    def update_playback_state(self, state):
        self.is_playing = state == QMediaPlayer.PlaybackState.PlayingState
        if self.is_playing:
            self.play_button.setText("Ⅱ")
            self.media_status.setText("Playing from FRIDAY")
            self.status_label.setText("STATUS: PLAYING")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.play_button.setText("▶")
            if self.current_index >= 0:
                self.media_status.setText("Paused")
                self.status_label.setText("STATUS: PAUSED")
        else:
            self.play_button.setText("▶")
            if self.current_index >= 0:
                self.media_status.setText("Stopped")
                self.status_label.setText("STATUS: STOPPED")

    def update_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.playlist:
            self.next_media()

    def update_duration(self, duration):
        self.seek_slider.setRange(0, duration)
        self.update_position(self.media_player.position())

    def update_position(self, position):
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position)
        self.track_position_label.setText(
            f"{self.format_time(position)} / {self.format_time(self.media_player.duration())}"
        )

    @staticmethod
    def format_time(milliseconds):
        seconds = max(0, milliseconds // 1000)
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def set_player_volume(self, value):
        self.audio_output.setVolume(value / 100)

    def handle_player_error(self, error, message):
        if error != QMediaPlayer.Error.NoError:
            self.media_status.setText(message or "Could not play this audio file")
            self.status_label.setText("STATUS: PLAYBACK ERROR")

    def send_system_media_key(self, key, action):
        try:
            pyautogui.press(key)
        except Exception as error:
            self.media_status.setText(f"System media key failed: {error}")
            self.status_label.setText("STATUS: MEDIA CONTROL ERROR")
            return False

        self.media_status.setText(f"Sent {action} to the active system player")
        self.status_label.setText(f"STATUS: SYSTEM {action.upper()} SENT")
        return True

    def next_media(self):
        if self.playlist:
            self.play_track((self.current_index + 1) % len(self.playlist))
        else:
            self.send_system_media_key("nexttrack", "next track")

    def previous_media(self):
        if self.playlist:
            if self.media_player.position() > 3000:
                self.media_player.setPosition(0)
            else:
                self.play_track((self.current_index - 1) % len(self.playlist))
        else:
            self.send_system_media_key("prevtrack", "previous track")

    # --------------------------------------------------
    # VOLUME
    # --------------------------------------------------

    def volume_up(self):
        if self.current_index >= 0:
            self.volume_slider.setValue(min(100, self.volume_slider.value() + 5))
            self.status_label.setText("STATUS: VOLUME UP")
        else:
            self.send_system_media_key("volumeup", "volume up")

    def volume_down(self):
        if self.current_index >= 0:
            self.volume_slider.setValue(max(0, self.volume_slider.value() - 5))
            self.status_label.setText("STATUS: VOLUME DOWN")
        else:
            self.send_system_media_key("volumedown", "volume down")

    def toggle_mute(self):
        if self.current_index >= 0:
            self.is_muted = not self.is_muted
            self.audio_output.setMuted(self.is_muted)
        else:
            if not self.send_system_media_key("volumemute", "mute toggle"):
                return
            self.is_muted = not self.is_muted

        self.mute_button.setText("UNMUTE" if self.is_muted else "MUTE")
        self.media_status.setText("Muted" if self.is_muted else "Audio restored")
        self.status_label.setText("STATUS: MUTED" if self.is_muted else "STATUS: AUDIO ACTIVE")

    def closeEvent(self, event):
        self.media_player.stop()
        event.accept()

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