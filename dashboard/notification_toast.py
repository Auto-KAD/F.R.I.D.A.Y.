import os
import sys
import subprocess
import threading
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QCursor


class NotificationToast(QWidget):
    """
    Sleek, floating on-screen toast notification.
    Stays on top without stealing window focus, animates smoothly,
    and automatically dismisses after a set duration.
    """

    def __init__(
        self,
        title="Screenshot Captured",
        message="Saved to data/screenshots",
        file_path=None,
        duration_ms=3000,
        parent=None
    ):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.file_path = file_path
        self.duration_ms = duration_ms

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._build_ui(title, message)
        self._position_on_screen()

        # Animations
        self._fade_in_anim = None
        self._fade_out_anim = None

    def _build_ui(self, title, message):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)

        # Card container
        self.card = QFrame(self)
        self.card.setObjectName("toastCard")
        self.card.setStyleSheet("""
            #toastCard {
                background-color: rgba(24, 44, 37, 245);
                border: 1.5px solid #47876A;
                border-radius: 14px;
            }
            #toastCard:hover {
                border: 1.5px solid #70C19B;
                background-color: rgba(28, 52, 44, 250);
            }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(shadow)

        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(16, 12, 18, 12)
        card_layout.setSpacing(14)

        # Camera Icon Badge
        icon_badge = QLabel("📸", self.card)
        icon_badge.setStyleSheet(
            "font-size: 24px; background: transparent; border: none;"
        )
        card_layout.addWidget(icon_badge)

        # Text column
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title_label = QLabel(title, self.card)
        title_label.setStyleSheet("""
            color: #E8F5E9;
            font-size: 13px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        text_layout.addWidget(title_label)

        sub_label = QLabel(message, self.card)
        sub_label.setStyleSheet("""
            color: #A3C9B8;
            font-size: 11px;
            font-weight: 400;
            background: transparent;
            border: none;
        """)
        sub_label.setWordWrap(True)
        text_layout.addWidget(sub_label)

        card_layout.addLayout(text_layout)

        # Close / dismiss hint button
        dismiss_btn = QLabel("✕", self.card)
        dismiss_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        dismiss_btn.setStyleSheet("""
            color: #6A9E88;
            font-size: 12px;
            font-weight: bold;
            background: transparent;
            border: none;
            padding: 2px 4px;
        """)
        dismiss_btn.mousePressEvent = lambda e: self.fade_out_and_close()
        card_layout.addWidget(dismiss_btn)

        root_layout.addWidget(self.card)

        # Make the whole card clickable if file_path is given
        if self.file_path and os.path.exists(self.file_path):
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.setToolTip("Click to reveal in folder")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.file_path and os.path.exists(self.file_path):
                self._reveal_file()
            self.fade_out_and_close()
        super().mousePressEvent(event)

    def _reveal_file(self):
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", "-R", self.file_path])
            elif sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{os.path.abspath(self.file_path)}"')
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(self.file_path)])
        except Exception as err:
            print("Failed to reveal screenshot:", err)

    def _position_on_screen(self):
        self.adjustSize()
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            # Top-right placement with 24px padding
            x = geo.right() - self.width() - 20
            y = geo.top() + 24
            self.move(x, y)

    def show_animated(self):
        self.setWindowOpacity(0.0)
        self.show()

        # Fade in
        self._fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in_anim.setDuration(220)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)
        self._fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_in_anim.start()

        # Schedule fade out
        QTimer.singleShot(self.duration_ms, self.fade_out_and_close)

        # Send system notification in background
        self._send_system_notification()

    def fade_out_and_close(self):
        if self._fade_out_anim is not None:
            return  # Already fading out

        self._fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_out_anim.setDuration(280)
        self._fade_out_anim.setStartValue(self.windowOpacity())
        self._fade_out_anim.setEndValue(0.0)
        self._fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out_anim.finished.connect(self._cleanup)
        self._fade_out_anim.start()

    def _cleanup(self):
        self.close()
        self.deleteLater()

    def _send_system_notification(self):
        def _notify():
            try:
                if sys.platform == "darwin":
                    msg = "Saved to data/screenshots"
                    if self.file_path:
                        msg = f"Saved: {os.path.basename(self.file_path)}"
                    cmd = [
                        "osascript",
                        "-e",
                        f'display notification "{msg}" with title "F.R.I.D.A.Y." subtitle "Screenshot Captured"'
                    ]
                    subprocess.run(cmd, capture_output=True, timeout=2)
            except Exception:
                pass

        threading.Thread(target=_notify, daemon=True).start()
