import os
import psutil
import pyautogui

from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QCursor, QFont, QPixmap, QPainter, QPainterPath, QImage, QColor, QPen, QBrush, QRadialGradient
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
    QStackedWidget
)

from dashboard.system_panel import SystemPanel
from dashboard.vision_studio import VisionStudio
from dashboard.gesture_lab import GestureLabPanel
from dashboard.media_controller import MediaController
from dashboard.tools import Tools
from dashboard.calendar import Calendar
from dashboard.chatbot import ChatbotPanel
from dashboard.jarvis import JarvisPanel
from dashboard.notes import NotesPanel
from dashboard.musical_instruments import MusicalInstrumentsPanel
from vision.desktop_gesture_worker import DesktopGestureWorker



class MeadowCompanion(QWidget):
    """Animated FRIDAY orb: blinks, smiles occasionally, and follows the cursor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(145, 135)
        self.setMouseTracking(True)
        self.eye_offset_x = 0.0
        self.eye_offset_y = 0.0
        self.blink = False
        self.smile = True
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink_once)
        self._blink_timer.start(2600)
        self._smile_timer = QTimer(self)
        self._smile_timer.timeout.connect(self._change_expression)
        self._smile_timer.start(5200)
        self._float_phase = 0
        self._motion_timer = QTimer(self)
        self._motion_timer.timeout.connect(self._animate)
        self._motion_timer.start(70)

    def _blink_once(self):
        self.blink = True
        self.update()
        QTimer.singleShot(150, self._open_eyes)

    def _open_eyes(self):
        self.blink = False
        self.update()

    def _change_expression(self):
        self.smile = not self.smile
        self.update()
        QTimer.singleShot(900, self._restore_smile)

    def _restore_smile(self):
        self.smile = True
        self.update()

    def _animate(self):
        self._float_phase = (self._float_phase + 1) % 360
        cursor = self.mapFromGlobal(QCursor.pos())
        center = self.rect().center()
        self._set_eye_direction(
            cursor.x() - center.x(),
            cursor.y() - center.y()
        )
        self.update()

    def _set_eye_direction(self, dx, dy):
        self.eye_offset_x = max(-4.0, min(4.0, dx / 24.0))
        self.eye_offset_y = max(-3.0, min(3.0, dy / 24.0))

    def mouseMoveEvent(self, event):
        center = self.rect().center()
        dx = event.position().x() - center.x()
        dy = event.position().y() - center.y()
        self._set_eye_direction(dx, dy)
        self.update()
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2 + (self._float_phase % 24 - 12) * 0.22
        radius = min(w, h) * 0.31

        glow = QRadialGradient(cx, cy, radius * 1.6)
        glow.setColorAt(0, QColor(131, 202, 218, 72))
        glow.setColorAt(0.62, QColor(201, 187, 227, 30))
        glow.setColorAt(1, QColor(201, 187, 227, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(int(cx-radius*1.6), int(cy-radius*1.6), int(radius*3.2), int(radius*3.2))

        painter.setPen(QPen(QColor('#8DBDB8'), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-14)
        painter.drawEllipse(int(-radius*1.48), int(-radius*0.34), int(radius*2.96), int(radius*0.68))
        painter.restore()

        orb_gradient = QRadialGradient(cx-radius*.34, cy-radius*.42, radius*1.6)
        orb_gradient.setColorAt(0, QColor('#FFF8DB'))
        orb_gradient.setColorAt(0.36, QColor('#F5D7E8'))
        orb_gradient.setColorAt(0.72, QColor('#A8D9E2'))
        orb_gradient.setColorAt(1, QColor('#769FC9'))
        painter.setPen(QPen(QColor('#FDFDF0'), 2))
        painter.setBrush(QBrush(orb_gradient))
        painter.drawEllipse(int(cx-radius), int(cy-radius), int(radius*2), int(radius*2))

        sheen = QRadialGradient(cx-radius*.46, cy-radius*.58, radius*.9)
        sheen.setColorAt(0, QColor(255, 255, 255, 150))
        sheen.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(sheen))
        painter.drawEllipse(int(cx-radius*.83), int(cy-radius*.88), int(radius*1.65), int(radius*1.65))

        painter.setBrush(QColor(224, 132, 150, 62))
        painter.drawEllipse(int(cx-radius*.69), int(cy+radius*.15), int(radius*.34), int(radius*.18))
        painter.drawEllipse(int(cx+radius*.35), int(cy+radius*.15), int(radius*.34), int(radius*.18))

        eye_y = cy - radius * 0.08
        eye_dx = radius * 0.34
        eye_width = radius * .25
        eye_height = radius * .31
        pupil_width = radius * .13
        pupil_height = radius * .17
        pupil_limit_x = (eye_width - pupil_width) / 2
        pupil_limit_y = (eye_height - pupil_height) / 2
        pupil_offset_x = max(-pupil_limit_x, min(pupil_limit_x, self.eye_offset_x))
        pupil_offset_y = max(-pupil_limit_y, min(pupil_limit_y, self.eye_offset_y))
        painter.setPen(Qt.PenStyle.NoPen)
        if self.blink:
            painter.setPen(QPen(QColor('#496C78'), max(2, int(radius*.055)), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(int(cx-eye_dx-radius*.10), int(eye_y), int(cx-eye_dx+radius*.10), int(eye_y))
            painter.drawLine(int(cx+eye_dx-radius*.10), int(eye_y), int(cx+eye_dx+radius*.10), int(eye_y))
        else:
            painter.setBrush(QColor('#FFFDF5'))
            painter.drawEllipse(int(cx-eye_dx-eye_width/2), int(eye_y-eye_height/2), int(eye_width), int(eye_height))
            painter.drawEllipse(int(cx+eye_dx-eye_width/2), int(eye_y-eye_height/2), int(eye_width), int(eye_height))
            painter.setBrush(QColor('#365D72'))
            left_pupil_x = cx - eye_dx + pupil_offset_x - pupil_width / 2
            right_pupil_x = cx + eye_dx + pupil_offset_x - pupil_width / 2
            pupil_top = eye_y + pupil_offset_y - pupil_height / 2
            painter.drawEllipse(int(left_pupil_x), int(pupil_top), int(pupil_width), int(pupil_height))
            painter.drawEllipse(int(right_pupil_x), int(pupil_top), int(pupil_width), int(pupil_height))
            painter.setBrush(QColor('#FFFFFF'))
            highlight_size = max(2, int(radius * .04))
            highlight_offset_x = pupil_width * .16
            highlight_offset_y = pupil_height * .18
            painter.drawEllipse(int(cx-eye_dx+pupil_offset_x-highlight_offset_x), int(eye_y+pupil_offset_y-highlight_offset_y), highlight_size, highlight_size)
            painter.drawEllipse(int(cx+eye_dx+pupil_offset_x-highlight_offset_x), int(eye_y+pupil_offset_y-highlight_offset_y), highlight_size, highlight_size)

        painter.setPen(QPen(QColor('#8B5E68'), max(2, int(radius*0.055)), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        if self.smile:
            smile = QPainterPath()
            smile.moveTo(cx-radius*.18, cy+radius*.22)
            smile.quadTo(cx, cy+radius*.43, cx+radius*.18, cy+radius*.22)
            painter.drawPath(smile)
        else:
            painter.drawLine(int(cx-radius*.12), int(cy+radius*.29), int(cx+radius*.12), int(cy+radius*.29))

        sprout_stem = QPainterPath()
        sprout_stem.moveTo(cx, cy-radius*.88)
        sprout_stem.quadTo(cx-radius*.02, cy-radius*1.04, cx+radius*.02, cy-radius*1.10)
        painter.setPen(QPen(QColor('#668E68'), max(2, int(radius*.045)), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(sprout_stem)
        for direction in (-1, 1):
            leaf = QPainterPath()
            leaf.moveTo(cx, cy-radius*1.01)
            leaf.quadTo(cx+direction*radius*.04, cy-radius*1.17, cx+direction*radius*.25, cy-radius*1.13)
            leaf.quadTo(cx+direction*radius*.20, cy-radius*.98, cx, cy-radius*1.01)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor('#83AE7C' if direction < 0 else '#A7C889'))
            painter.drawPath(leaf)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#F4C77A'))
        for sx, sy, size in [(-1.18, -.72, 3), (1.23, -.48, 3), (-1.05, .78, 2), (1.08, .82, 2)]:
            painter.drawEllipse(int(cx+sx*radius-size), int(cy+sy*radius-size), size*2, size*2)


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
        self.musical_instruments = None

        # ==================================================
        # CHATBOT
        # ==================================================

        self.chatbot = None

        self.gesture_lab = None
        self.gesture_worker = None

        self.setWindowTitle("FRIDAY")

        self.setup_ui()

        self.start_system_monitor()
        self.start_gesture_control()

    # ======================================================
    # MAIN UI
    # ======================================================

    def setup_ui(self):
        self.setMinimumSize(800, 560)
        self.setObjectName("dashboardRoot")
        self.setWindowTitle("F.R.I.D.A.Y. — Cloud Garden")

        root = QHBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(12)
        self.root_layout = root

        # Left navigation rail
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(204)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(12, 16, 12, 14)
        side.setSpacing(5)
        brand = QLabel("✦ F.R.I.D.A.Y.")
        brand.setObjectName("brand")
        brand.setFont(QFont("Georgia", 14, QFont.Weight.Bold))
        side.addWidget(brand)
        tagline = QLabel("YOUR CLOUD GARDEN")
        tagline.setObjectName("eyebrow")
        side.addWidget(tagline)
        side.addSpacing(10)
        self.navigation_buttons = {}
        for icon, name, callback in [
            ("⌂", "Home", self.show_idle), ("◎", "Vision Studio", self.open_vision_studio),
            ("♧", "Gesture Lab", self.open_gesture_lab), ("♫", "Media", self.open_media_controller),
            ("♫", "Musical Instruments", self.open_musical_instruments),
            ("▦", "Calendar", self.open_calendar), ("✧", "Tools", self.open_tools),
            ("⚙", "System", self.open_system_panel),
            ("▤", "Notes", self.open_notes), ("◇", "JARVIS", self.open_jarvis)]:
            b = QPushButton(f"{icon}   {name}")
            b.setObjectName("navActive" if name == "Home" else "navButton")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setMinimumHeight(42)
            b.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
            b.clicked.connect(callback)
            side.addWidget(b)
            self.navigation_buttons[name] = b
        side.addStretch(1)
        note = QLabel("“Little steps,\nbig magic.” ✧")
        note.setObjectName("sideNote")
        note.setWordWrap(True)
        side.addWidget(note)
        root.addWidget(self.sidebar)

        # Main content column
        main_col = QVBoxLayout()
        main_col.setSpacing(9)
        self.main_col = main_col
        root.addLayout(main_col, 1)

        top = QHBoxLayout()
        greeting_box = QVBoxLayout()
        greeting = QLabel(f"Good day, {self.username.title()}! ✿")
        greeting.setObjectName("greeting")
        greeting.setFont(QFont("Trebuchet MS", 23, QFont.Weight.DemiBold))
        subtitle = QLabel("A softer start, a brighter day.")
        subtitle.setObjectName("mutedText")
        greeting_box.addWidget(greeting)
        greeting_box.addWidget(subtitle)
        top.addLayout(greeting_box, 1)

        status_box = QFrame()
        status_box.setObjectName("glassCard")
        status_box.setMinimumWidth(172)
        status_layout = QVBoxLayout(status_box)
        status_layout.setContentsMargins(12, 8, 12, 8)
        self.system_label = QLabel("CPU  --%   •   RAM  --%")
        self.clock_label = QLabel("--:--")
        online = QLabel("●  ONLINE · READY")
        online.setObjectName("onlineLabel")
        status_layout.addWidget(online, alignment=Qt.AlignmentFlag.AlignRight)
        status_layout.addWidget(self.system_label, alignment=Qt.AlignmentFlag.AlignRight)
        status_layout.addWidget(self.clock_label, alignment=Qt.AlignmentFlag.AlignRight)
        top.addWidget(status_box)
        main_col.addLayout(top)

        workspace = QFrame()
        workspace.setObjectName("heroCard")
        self.hero_layout = QVBoxLayout(workspace)
        self.hero_layout.setContentsMargins(12, 10, 12, 10)
        self.hero_layout.setSpacing(0)
        self.workspace_stack = QStackedWidget()
        self.workspace_stack.setObjectName("workspaceStack")
        self.hero_layout.addWidget(self.workspace_stack, 1)

        self.idle_page = QWidget()
        self.idle_layout = QVBoxLayout(self.idle_page)
        self.idle_layout.setContentsMargins(0, 0, 0, 0)
        self.idle_layout.setSpacing(10)

        # Center idle view with animated companion
        hero = QFrame()
        hero.setObjectName("idleHero")
        idle_hero_layout = QVBoxLayout(hero)
        idle_hero_layout.setContentsMargins(18, 8, 18, 10)
        idle_hero_layout.setSpacing(3)
        idle_hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.companion = MeadowCompanion()
        self.companion.setMaximumSize(300, 270)
        self.companion.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        idle_hero_layout.addWidget(self.companion, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        companion_title = QLabel("A little magic, right here")
        companion_title.setObjectName("heroTitle")
        companion_title.setFont(QFont("Trebuchet MS", 20, QFont.Weight.DemiBold))
        companion_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_hero_layout.addWidget(companion_title)
        self.assistant_message = QLabel("I'm here for you. Take a breath and let's make something.")
        self.assistant_message.setObjectName("mutedText")
        self.assistant_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_hero_layout.addWidget(self.assistant_message)
        self.idle_layout.addWidget(hero, 1)

        # Lower cards: today / camera state
        lower = QHBoxLayout()
        lower.setSpacing(12)
        today = QFrame()
        today.setObjectName("glassCard")
        today_layout = QVBoxLayout(today)
        today_layout.setContentsMargins(14, 10, 14, 10)
        today_title = QLabel("🌱  TODAY, IN BLOOM")
        today_title.setObjectName("eyebrow")
        today_layout.addWidget(today_title)
        today_layout.addWidget(QLabel("A little progress is still progress."))
        today_layout.addWidget(QLabel("✦  Create something • Take a breath • Keep going"))
        lower.addWidget(today, 1)

        camera_card = QFrame()
        camera_card.setObjectName("glassCard")
        camera_layout = QVBoxLayout(camera_card)
        camera_layout.setContentsMargins(12, 10, 12, 10)
        camera_title = QLabel("✧  HAND TRACKING")
        camera_title.setObjectName("eyebrow")
        camera_layout.addWidget(camera_title)
        self.camera_preview = QLabel("OPEN GESTURE LAB TO START")
        self.camera_preview.setObjectName("cameraPreview")
        self.camera_preview.setMinimumSize(165, 76)
        self.camera_preview.setMaximumSize(280, 118)
        self.camera_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        camera_layout.addWidget(self.camera_preview, alignment=Qt.AlignmentFlag.AlignCenter)
        self.gesture_status_label = QLabel("GESTURE CONTROL • OFF")
        self.gesture_status_label.setObjectName("mutedText")
        self.gesture_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_layout.addWidget(self.gesture_status_label)
        lower.addWidget(camera_card)
        self.idle_layout.addLayout(lower)
        self.workspace_stack.addWidget(self.idle_page)
        main_col.addWidget(workspace, 1)

        self.setStyleSheet("""
            QWidget#dashboardRoot { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #DCEFF0, stop:0.48 #EEF3E5, stop:1 #F8E5D8); }
            QWidget { color: #35565A; font-family: 'Segoe UI'; font-size: 10pt; }
            QFrame#sidebar, QFrame#glassCard, QFrame#heroCard {
                background-color: rgba(255, 253, 246, 226); border: 1px solid #D7E2D8; border-radius: 16px;
            }
            QFrame#sidebar { background-color: rgba(255, 251, 240, 240); border-color: #D8DFCC; }
            QFrame#heroCard { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255, 255, 250, 238), stop:1 rgba(225, 242, 232, 226)); border-color: #C8DED5; }
            QFrame#idleHero { background: transparent; border: none; }
            QStackedWidget#workspaceStack { background: transparent; border: none; }
            QLabel { background: transparent; color: #35565A; }
            QLabel#brand { color: #376D68; font-family: 'Georgia'; font-size: 14pt; font-weight: bold; }
            QLabel#eyebrow { color: #64856E; font-size: 9pt; font-weight: bold; }
            QLabel#greeting { color: #31585A; font-family: 'Georgia'; font-size: 23pt; font-weight: 600; }
            QLabel#mutedText, QLabel#sideNote { color: #71877A; }
            QLabel#onlineLabel { color: #47876A; font-weight: bold; }
            QLabel#heroTitle { color: #4C7771; font-family: 'Georgia'; font-size: 20pt; font-weight: 600; }
            QPushButton { background-color: rgba(255, 255, 250, 238); color: #365D5E; border: 1px solid #D1DDD2; border-radius: 12px; padding: 11px 14px; font-size: 11pt; }
            QPushButton:hover { background-color: #E5F1E6; border: 1px solid #9FC4AE; }
            QPushButton:pressed { background-color: #D6E8D9; }
            QPushButton#navButton { text-align: left; padding: 10px 11px; background: transparent; border-color: transparent; }
            QPushButton#navButton:hover { background-color: #E8F1E5; border-color: #D4E1D1; }
            QPushButton#navActive { text-align: left; padding: 10px 11px; background-color: #DCEBDD; border-color: #C5DCC9; color: #376D68; font-weight: bold; }
            QLabel#cameraPreview { background-color: #DCEBE7; border: 1px solid #C4DAD2; border-radius: 11px; color: #607F79; font-size: 9pt; }
            QPushButton#markLvButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #376D68, stop:1 #47876A);
                color: #ffffff;
                border: 1px solid #2d5a55;
                border-radius: 14px;
                font-family: 'Segoe UI';
                font-size: 10pt;
                font-weight: 600;
                padding: 7px 18px;
            }
            QPushButton#markLvButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #42827c, stop:1 #539d7c);
                border: 1px solid #3d7973;
            }
            QPushButton#markLvButton:pressed {
                background-color: #2b5652;
            }
        """)
        self.apply_responsive_layout()

    def apply_responsive_layout(self):
        width = max(self.width(), self.minimumWidth())
        height = max(self.height(), self.minimumHeight())
        compact = height < 780 or width < 1180

        margin = 10 if compact else 16
        self.root_layout.setContentsMargins(margin, margin, margin, margin)
        self.root_layout.setSpacing(9 if compact else 13)
        self.main_col.setSpacing(7 if compact else 11)
        self.sidebar.setFixedWidth(170 if width < 1000 else 190 if compact else 204)
        self.hero_layout.setContentsMargins(14, 5 if compact else 10, 14, 7 if compact else 12)
        self.hero_layout.setSpacing(2 if compact else 4)

        companion_height = max(180, min(300, int(height * 0.36)))
        companion_width = min(316, int(companion_height * 1.05))
        self.companion.setFixedSize(companion_width, companion_height)

        for button in self.navigation_buttons.values():
            nav_height = 34 if height < 620 else 44 if compact else 52
            button.setMinimumHeight(nav_height)
            button.setFont(QFont("Segoe UI", 10 if compact else 11, QFont.Weight.DemiBold))
        self.camera_preview.setMinimumSize(150, 68 if compact else 92)
        self.camera_preview.setMaximumHeight(94 if compact else 120)

    def open_chatbot_from_nav(self):
        self.open_chatbot()

    def _set_active_navigation(self, name):
        for button_name, button in self.navigation_buttons.items():
            button.setObjectName("navActive" if button_name == name else "navButton")
            button.style().unpolish(button)
            button.style().polish(button)

    def _show_workspace_page(self, page, navigation_name):
        if self.workspace_stack.indexOf(page) == -1:
            self.workspace_stack.addWidget(page)
            return_home = getattr(page, "return_home_requested", None)
            if return_home is not None:
                return_home.connect(self.show_idle)

        page.setMinimumSize(0, 0)
        page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Intelligently manage camera feed between tools
        is_camera_page = (page is self.vision_studio or (hasattr(self, "musical_instruments") and page is self.musical_instruments))

        # Stop previous camera consumers if navigating away
        if hasattr(self, "musical_instruments") and self.musical_instruments is not None and page is not self.musical_instruments:
            self.musical_instruments.stop_camera()
        if self.vision_studio is not None and page is not self.vision_studio:
            self.vision_studio.stop_camera()

        if is_camera_page:
            self.stop_gesture_control()

        self.workspace_stack.setCurrentWidget(page)
        page.show()

        if is_camera_page and hasattr(page, "start_camera"):
            page.start_camera()

        if not is_camera_page:
            self.start_gesture_control()
        self._set_active_navigation(navigation_name)

    def show_idle(self):
        self._show_workspace_page(self.idle_page, "Home")

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
                background-color: #F0EEFF;
                border: 1px solid #D8DDF5;
                border-radius: 27px;
                font-size: 25px;
            }
        """)

    # ======================================================
    # CHATBOT TOGGLE
    # ======================================================

    def open_chatbot(self):
        if self.chatbot is None:
            self.chatbot = ChatbotPanel(self.username)
            self.chatbot.close_requested.connect(self.close_chatbot)
        self._show_workspace_page(self.chatbot, None)

    def toggle_chatbot(self):

        if (
            self.chatbot is not None
            and self.workspace_stack.currentWidget() is self.chatbot
        ):
            self.close_chatbot()
            return

        self.open_chatbot()

    # ======================================================
    # CLOSE CHATBOT
    # ======================================================

    def close_chatbot(self):

        if self.chatbot:

            self.chatbot.stop_all()
        self.show_idle()

    # ======================================================
    # ======================================================
    # GESTURE CONTROL
    # ======================================================

    def start_gesture_control(self):
        if self.gesture_worker is not None:
            return

        self.gesture_status_label.setText("GESTURE CONTROL • STARTING")
        self.camera_preview.setText("CAMERA STARTING…")
        self.gesture_worker = DesktopGestureWorker()
        self.gesture_worker.gesture_detected.connect(self.handle_gesture)
        self.gesture_worker.camera_frame.connect(self.update_camera_preview)
        self.gesture_worker.error_occurred.connect(self.handle_gesture_error)
        self.gesture_worker.start()

    def stop_gesture_control(self):
        if self.gesture_worker is None:
            return

        worker = self.gesture_worker
        self.gesture_worker = None
        worker.stop()
        self.camera_preview.clear()
        self.camera_preview.setText("CAMERA RESERVED FOR VISION STUDIO")
        self.update_gesture_status("GESTURE CONTROL • PAUSED")

    def update_camera_preview(self, frame):
        height, width, channels = frame.shape
        image = QImage(
            frame.data,
            width,
            height,
            channels * width,
            QImage.Format.Format_RGB888
        ).copy()
        pixmap = QPixmap.fromImage(image).scaled(
            self.camera_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.camera_preview.setPixmap(pixmap)

    def handle_gesture_error(self, message):
        self.update_gesture_status("GESTURE CONTROL • CAMERA ERROR")
        self.camera_preview.setText(f"CAMERA ERROR\n{message}")
        print("FRIDAY gesture error:", message)

    def update_gesture_status(self, message):
        self.gesture_status_label.setText(message)

    def handle_gesture(self, gesture):

        if self.gesture_lab is not None:
            self.gesture_lab.set_gesture_name(gesture)
        self.update_gesture_status(
            f"GESTURE CONTROL • {gesture.replace('_', ' ')}"
        )

        if gesture == "TWO_FINGER":
            self.toggle_chatbot()

        elif gesture == "OPEN_PALM":
            try:
                pyautogui.click()
                self.update_gesture_status("OPEN PALM • TARGET ACTIVATED")
            except Exception as error:
                self.update_gesture_status("OPEN PALM • CLICK FAILED")
                print("FRIDAY open-palm action error:", error)

        elif gesture == "FIST":
            self.close_active_application()

        elif gesture == "TWO_THUMBS_UP":
            self.take_screenshot()

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

            self.update_gesture_status("GESTURE CONTROL • SCREENSHOT SAVED ✓")

            print("FRIDAY screenshot saved:", screenshot_path)
        except Exception as error:
            self.update_gesture_status("GESTURE CONTROL • SCREENSHOT FAILED")
            print("FRIDAY screenshot error:", error)

    def close_active_application(self):
        self.show_idle()

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
        self._show_workspace_page(self.system_panel, "System")

    def open_vision_studio(self):
        if self.vision_studio is None:

            self.vision_studio = VisionStudio()
        self._show_workspace_page(self.vision_studio, "Vision Studio")

    def open_gesture_lab(self):
        if self.gesture_lab is None:
            self.gesture_lab = GestureLabPanel()
        self._show_workspace_page(self.gesture_lab, "Gesture Lab")

    def open_media_controller(self):

        if self.media_controller is None:

            self.media_controller = MediaController()
        self._show_workspace_page(self.media_controller, "Media")

    def open_musical_instruments(self):
        if not hasattr(self, "musical_instruments") or self.musical_instruments is None:
            self.musical_instruments = MusicalInstrumentsPanel()
        self._show_workspace_page(self.musical_instruments, "Musical Instruments")

    def open_tools(self):

        if self.tools is None:

            self.tools = Tools()
        self._show_workspace_page(self.tools, "Tools")

    def open_calendar(self):

        if self.calendar is None:

            self.calendar = Calendar()
        self._show_workspace_page(self.calendar, "Calendar")

    def open_notes(self):
        if not hasattr(self, "notes_panel"):
            self.notes_panel = NotesPanel()
        self._show_workspace_page(self.notes_panel, "Notes")

    def open_jarvis(self):
        self.launch_mark_lv()

    def launch_mark_lv(self):
        import subprocess
        import sys
        from PyQt6.QtWidgets import QApplication

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mark_lv_dir = os.path.join(base_dir, "Mark-LV-main")
        mark_lv_script = os.path.join(mark_lv_dir, "main.py")

        venv_python = os.path.join(base_dir, ".venv", "bin", "python")
        if not os.path.exists(venv_python):
            venv_python_win = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
            if os.path.exists(venv_python_win):
                venv_python = venv_python_win
            else:
                venv_python = sys.executable

        # Cleanly release camera and gestures before launching Mark LV
        self.stop_gesture_control()

        # Launch Mark LV concurrently in detached process
        try:
            if sys.platform == "win32":
                subprocess.Popen(
                    [venv_python, mark_lv_script],
                    cwd=mark_lv_dir,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                subprocess.Popen(
                    [venv_python, mark_lv_script],
                    cwd=mark_lv_dir,
                    start_new_session=True
                )
        except Exception as e:
            print(f"Failed to launch Mark LV: {e}")

        # Concurrently close FRIDAY
        self.close()
        app = QApplication.instance()
        if app is not None:
            QTimer.singleShot(100, app.quit)

    # ======================================================
    # RESIZE
    # ======================================================

    def resizeEvent(self, event):

        super().resizeEvent(
            event
        )

        self.apply_responsive_layout()

        if hasattr(self, "workspace_stack"):
            self.workspace_stack.updateGeometry()

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

        self.stop_gesture_control()

        if hasattr(
            self,
            "timer"
        ):

            self.timer.stop()


        if self.system_panel:

            self.system_panel.close()

        if self.vision_studio:

            self.vision_studio.close()

        if self.gesture_lab:

            self.gesture_lab.close()

        if self.media_controller:

            self.media_controller.close()

        if self.tools:

            self.tools.close()

        if self.calendar:

            self.calendar.close()

        if self.chatbot:

            self.chatbot.close()

        if hasattr(self, "musical_instruments") and self.musical_instruments is not None:
            self.musical_instruments.stop_camera()
            self.musical_instruments.close()

        event.accept()