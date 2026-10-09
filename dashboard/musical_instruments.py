import os
import time
import cv2
import numpy as np
import pygame

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy
)

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp

from dashboard.theme import apply_cloud_garden_theme


class MusicalInstrumentsPanel(QWidget):
    return_home_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("musicalInstrumentsPanel")

        self.current_instrument = "PIANO"  # "PIANO", "GUITAR", "TABLA"
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._process_frame)

        self.detector = None
        self.last_timestamp_ms = 0
        self.start_time = time.time()

        # State tracking for instruments
        self.previous_note = None
        self.active_note = None
        self.note_hit_time = 0

        self._init_audio()
        self._init_hand_detector()
        self.setup_ui()

    # =========================================================
    # AUDIO SYNTHESIS
    # =========================================================

    def _init_audio(self):
        """Pre-synthesizes high quality instrument samples using Pygame Mixer."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception as e:
            print(f"[Instruments] Audio mixer init error: {e}")

        self.piano_sounds = {}
        self.guitar_sounds = {}
        self.tabla_sounds = {}

        sample_rate = 44100

        # 1. PIANO SOUNDS (C, D, E, F, G, A, B)
        piano_freqs = {
            "C": 261.63,
            "D": 293.66,
            "E": 329.63,
            "F": 349.23,
            "G": 392.00,
            "A": 440.00,
            "B": 493.88
        }
        for note, freq in piano_freqs.items():
            duration = 0.7
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # Add harmonics for piano warmth
            wave = (
                np.sin(2 * np.pi * freq * t)
                + 0.35 * np.sin(2 * np.pi * freq * 2 * t)
                + 0.15 * np.sin(2 * np.pi * freq * 3 * t)
            )
            envelope = np.exp(-4.2 * t)
            wave = (wave * envelope)
            max_val = np.max(np.abs(wave))
            if max_val > 0:
                wave = wave / max_val
            audio = (wave * 32767).astype(np.int16)
            stereo = np.column_stack((audio, audio))
            try:
                self.piano_sounds[note] = pygame.sndarray.make_sound(stereo)
            except Exception:
                pass

        # 2. GUITAR SOUNDS (E_low, A, D, G, B, E_high)
        guitar_freqs = {
            "E (Low)": 82.41,
            "A": 110.00,
            "D": 146.83,
            "G": 196.00,
            "B": 246.94,
            "E (High)": 329.63
        }
        for note, freq in guitar_freqs.items():
            duration = 0.9
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave = (
                np.sin(2 * np.pi * freq * t)
                + 0.50 * np.sin(2 * np.pi * freq * 2 * t)
                + 0.25 * np.sin(2 * np.pi * freq * 3 * t)
                + 0.12 * np.sin(2 * np.pi * freq * 4 * t)
            )
            envelope = np.exp(-2.8 * t)
            wave = (wave * envelope)
            max_val = np.max(np.abs(wave))
            if max_val > 0:
                wave = wave / max_val
            audio = (wave * 32767).astype(np.int16)
            stereo = np.column_stack((audio, audio))
            try:
                self.guitar_sounds[note] = pygame.sndarray.make_sound(stereo)
            except Exception:
                pass

        # 3. TABLA SOUNDS (DHA, DHI, NA, TIN)
        def _make_tabla_sample(freq, duration, decay, noise_ratio=0.12):
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave = np.sin(2 * np.pi * freq * t)
            envelope = np.exp(-decay * t)
            noise = np.random.uniform(-1, 1, len(t))
            wave = (wave + noise_ratio * noise) * envelope
            max_val = np.max(np.abs(wave))
            if max_val > 0:
                wave = wave / max_val
            audio = (wave * 32767).astype(np.int16)
            stereo = np.column_stack((audio, audio))
            try:
                return pygame.sndarray.make_sound(stereo)
            except Exception:
                return None

        self.tabla_sounds["DHA"] = _make_tabla_sample(118, 0.50, 7.0, 0.10)
        self.tabla_sounds["DHI"] = _make_tabla_sample(180, 0.35, 9.0, 0.12)
        self.tabla_sounds["NA"]  = _make_tabla_sample(400, 0.30, 11.0, 0.08)
        self.tabla_sounds["TIN"] = _make_tabla_sample(600, 0.25, 13.0, 0.05)

    def _play_sound(self, category, name):
        """Plays a pre-rendered sound cleanly."""
        try:
            sound = None
            if category == "PIANO":
                sound = self.piano_sounds.get(name)
            elif category == "GUITAR":
                sound = self.guitar_sounds.get(name)
            elif category == "TABLA":
                sound = self.tabla_sounds.get(name)
            if sound:
                sound.play()
        except Exception as e:
            print(f"[Instruments] Play sound error: {e}")

    # =========================================================
    # MEDIAPIPE DETECTOR
    # =========================================================

    def _init_hand_detector(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_paths = [
            os.path.join(base_dir, "instruments", "hand_landmarker.task"),
            os.path.join(base_dir, "models", "hand_landmarker.task"),
        ]
        chosen_path = None
        for p in model_paths:
            if os.path.exists(p):
                chosen_path = p
                break

        if not chosen_path:
            print("[Instruments] Error: hand_landmarker.task not found!")
            return

        try:
            base_options = python.BaseOptions(model_asset_path=chosen_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=1,
                min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.6,
                min_tracking_confidence=0.6,
                running_mode=vision.RunningMode.VIDEO
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            self.start_time = time.time()
        except Exception as e:
            print(f"[Instruments] Failed to initialize MediaPipe HandLandmarker: {e}")

    # =========================================================
    # UI SETUP
    # =========================================================

    def setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 14, 20, 14)
        root_layout.setSpacing(10)

        # Header bar
        header = QHBoxLayout()
        header.setSpacing(12)

        title_box = QVBoxLayout()
        title = QLabel("MUSICAL INSTRUMENTS")
        title.setFont(QFont("Georgia", 22, QFont.Weight.Bold))
        subtitle = QLabel("Air Piano • Air Guitar • Air Tabla — Hand-tracked Virtual Instruments")
        subtitle.setObjectName("eyebrow")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)

        # Instrument Selector Tabs
        selector_frame = QFrame()
        selector_frame.setObjectName("selectorCard")
        selector_layout = QHBoxLayout(selector_frame)
        selector_layout.setContentsMargins(6, 4, 6, 4)
        selector_layout.setSpacing(6)

        self.tab_buttons = {}
        for key, label in [("PIANO", "🎹 Air Piano"), ("GUITAR", "🎸 Air Guitar"), ("TABLA", "🪘 Air Tabla")]:
            btn = QPushButton(label)
            btn.setObjectName("instTabActive" if key == self.current_instrument else "instTab")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self.set_instrument(k))
            selector_layout.addWidget(btn)
            self.tab_buttons[key] = btn

        header.addWidget(selector_frame)

        # Return to idle button
        back_btn = QPushButton("← Return Home")
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.return_home_requested.emit)
        header.addWidget(back_btn)

        root_layout.addLayout(header)

        # Video frame container
        video_card = QFrame()
        video_card.setObjectName("heroCard")
        video_card_layout = QVBoxLayout(video_card)
        video_card_layout.setContentsMargins(10, 8, 10, 8)
        video_card_layout.setSpacing(6)

        self.video_label = QLabel("CAMERA INITIALIZING...")
        self.video_label.setObjectName("videoPreview")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setMinimumSize(640, 420)
        video_card_layout.addWidget(self.video_label, 1)

        # Bottom status readout
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(8, 0, 8, 0)
        self.status_label = QLabel("Hover your index finger over notes to play • Real-time Optical Tracking Active")
        self.status_label.setObjectName("mutedText")
        self.hit_label = QLabel("NO NOTE PLAYED")
        self.hit_label.setObjectName("hitDisplay")
        self.hit_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.hit_label, 0, Qt.AlignmentFlag.AlignRight)

        video_card_layout.addLayout(status_layout)
        root_layout.addWidget(video_card, 1)

        apply_cloud_garden_theme(self, """
            QFrame#selectorCard {
                background-color: rgba(255, 253, 246, 210);
                border: 1px solid #D7E2D8;
                border-radius: 14px;
            }
            QPushButton#instTab {
                background-color: transparent;
                color: #4C7771;
                border: 1px solid transparent;
                border-radius: 10px;
                padding: 7px 16px;
                font-weight: 600;
                font-size: 10pt;
            }
            QPushButton#instTab:hover {
                background-color: #E8F1E5;
                border-color: #D4E1D1;
            }
            QPushButton#instTabActive {
                background-color: #376D68;
                color: #ffffff;
                border: 1px solid #2B5752;
                border-radius: 10px;
                padding: 7px 16px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton#backButton {
                background-color: rgba(255, 255, 250, 238);
                color: #365D5E;
                border: 1px solid #D1DDD2;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton#backButton:hover {
                background-color: #E5F1E6;
                border-color: #9FC4AE;
            }
            QLabel#videoPreview {
                background-color: #121A18;
                border: 1px solid #C4DAD2;
                border-radius: 14px;
                color: #A3C5BA;
                font-size: 12pt;
                font-weight: bold;
            }
            QLabel#hitDisplay {
                color: #2F6F5A;
                padding: 2px 10px;
                background-color: #DCEBDD;
                border-radius: 8px;
            }
        """)

    def set_instrument(self, name):
        self.current_instrument = name
        self.previous_note = None
        self.active_note = None
        for key, btn in self.tab_buttons.items():
            btn.setObjectName("instTabActive" if key == name else "instTab")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        descriptions = {
            "PIANO": "PIANO: Move index finger down onto the piano keys (C, D, E, F, G, A, B).",
            "GUITAR": "GUITAR: Pluck the 6 strings (E, A, D, G, B, E) by crossing them horizontally.",
            "TABLA": "TABLA: Strike the center Syahi for DHA, outer rim for TIN, left for DHI, right for NA."
        }
        self.status_label.setText(descriptions.get(name, ""))
        self.hit_label.setText("READY")

    # =========================================================
    # CAMERA LIFECYCLE MANAGEMENT
    # =========================================================

    def showEvent(self, event):
        super().showEvent(event)
        self.start_camera()

    def hideEvent(self, event):
        self.stop_camera()
        super().hideEvent(event)

    def start_camera(self):
        """Starts exclusive camera feed for the instrument."""
        if self.cap is not None and self.cap.isOpened():
            return

        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.video_label.setText("⚠️ Webcam could not be opened.\nEnsure no other app is using the camera.")
                return

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.start_time = time.time()
            self.timer.start(30)  # ~33 FPS
        except Exception as e:
            self.video_label.setText(f"Camera error: {e}")

    def stop_camera(self):
        """Releases the camera feed cleanly so other components can access it."""
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()

        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self.previous_note = None
        self.active_note = None

    # =========================================================
    # FRAME PROCESSING & INSTRUMENT LOGIC
    # =========================================================

    def _process_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return

        # Mirror video
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Detect Hand Landmarks
        results = None
        if self.detector is not None:
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                ts = int((time.time() - self.start_time) * 1000)
                if ts <= self.last_timestamp_ms:
                    ts = self.last_timestamp_ms + 1
                self.last_timestamp_ms = ts
                results = self.detector.detect_for_video(mp_image, ts)
            except Exception as e:
                # Video timestamp or processing glitch
                pass

        # Fingertip position
        fingertip = None
        if results and results.hand_landmarks:
            hand = results.hand_landmarks[0]
            tip = hand[8]  # Index fingertip
            fingertip = (int(tip.x * w), int(tip.y * h))

            # Draw hand skeleton
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (0, 5), (5, 6), (6, 7), (7, 8),
                (5, 9), (9, 10), (10, 11), (11, 12),
                (9, 13), (13, 14), (14, 15), (15, 16),
                (13, 17), (17, 18), (18, 19), (19, 20),
                (0, 17)
            ]
            for start_idx, end_idx in connections:
                pt1 = (int(hand[start_idx].x * w), int(hand[start_idx].y * h))
                pt2 = (int(hand[end_idx].x * w), int(hand[end_idx].y * h))
                cv2.line(frame, pt1, pt2, (120, 240, 160), 2)

            for lm in hand:
                cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 4, (60, 200, 120), -1)

            # Glowing fingertip
            cv2.circle(frame, fingertip, 12, (255, 210, 60), -1)
            cv2.circle(frame, fingertip, 16, (255, 255, 255), 2)

        # Route to active instrument logic
        current_hit = None
        if self.current_instrument == "PIANO":
            current_hit = self._draw_and_play_piano(frame, w, h, fingertip)
        elif self.current_instrument == "GUITAR":
            current_hit = self._draw_and_play_guitar(frame, w, h, fingertip)
        elif self.current_instrument == "TABLA":
            current_hit = self._draw_and_play_tabla(frame, w, h, fingertip)

        # Update note hit display
        if current_hit:
            self.hit_label.setText(f"PLAYING: {current_hit}")
        elif self.previous_note:
            self.hit_label.setText(f"LAST: {self.previous_note}")

        # Render frame onto QLabel
        rgb_disp = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb_disp.data, w, h, w * 3, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(
            pix.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    # ---------------------------------------------------------
    # 1. PIANO RENDER & TRIGGER
    # ---------------------------------------------------------
    def _draw_and_play_piano(self, frame, w, h, fingertip):
        keys = ["C", "D", "E", "F", "G", "A", "B"]
        key_width = w // 7
        key_height = int(h * 0.38)
        piano_y = h - key_height

        detected_key = None
        if fingertip:
            fx, fy = fingertip
            if fy >= piano_y:
                idx = fx // key_width
                if 0 <= idx < 7:
                    detected_key = keys[idx]

        # Draw piano keys
        for i, key in enumerate(keys):
            x1 = i * key_width
            x2 = (i + 1) * key_width

            is_active = (key == detected_key)
            fill_color = (120, 230, 255) if is_active else (245, 248, 250)

            # Key body
            cv2.rectangle(frame, (x1, piano_y), (x2, h), fill_color, -1)
            # Key border
            cv2.rectangle(frame, (x1, piano_y), (x2, h), (40, 55, 50), 2)

            # Note label
            cv2.putText(
                frame,
                key,
                (x1 + key_width // 2 - 12, h - 25),
                cv2.FONT_HERSHEY_DUPLEX,
                1.0,
                (30, 60, 50) if not is_active else (10, 40, 150),
                2
            )

        # Trigger sound on new key press
        if detected_key is not None:
            if detected_key != self.previous_note:
                self._play_sound("PIANO", detected_key)
                self.previous_note = detected_key
        else:
            self.previous_note = None

        return detected_key

    # ---------------------------------------------------------
    # 2. GUITAR RENDER & TRIGGER
    # ---------------------------------------------------------
    def _draw_and_play_guitar(self, frame, w, h, fingertip):
        string_names = ["E (High)", "B", "G", "D", "A", "E (Low)"]
        string_spacing = 38
        center_y = h // 2

        # Draw wooden guitar neck frame
        neck_x1, neck_x2 = 60, w - 60
        neck_y1 = center_y - int(3.2 * string_spacing)
        neck_y2 = center_y + int(3.2 * string_spacing)

        cv2.rectangle(frame, (neck_x1, neck_y1), (neck_x2, neck_y2), (40, 50, 65), -1)
        cv2.rectangle(frame, (neck_x1, neck_y1), (neck_x2, neck_y2), (180, 205, 215), 3)

        # Draw frets
        for fx in range(neck_x1 + 80, neck_x2, 100):
            cv2.line(frame, (fx, neck_y1), (fx, neck_y2), (80, 100, 120), 2)

        string_positions = []
        for i in range(6):
            sy = center_y - int(2.5 * string_spacing) + i * string_spacing
            string_positions.append(sy)

        detected_string = None
        if fingertip:
            fx, fy = fingertip
            if neck_x1 <= fx <= neck_x2:
                for i, sy in enumerate(string_positions):
                    if abs(fy - sy) < 16:
                        detected_string = string_names[i]
                        break

        # Draw 6 strings
        for i, sy in enumerate(string_positions):
            name = string_names[i]
            is_active = (name == detected_string)
            col = (60, 255, 220) if is_active else (225, 235, 240)
            thickness = 4 if is_active else 2

            cv2.line(frame, (neck_x1, sy), (neck_x2, sy), col, thickness)
            cv2.putText(
                frame,
                name,
                (neck_x2 - 110, sy - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                col,
                2
            )

        if detected_string is not None:
            if detected_string != self.previous_note:
                self._play_sound("GUITAR", detected_string)
                self.previous_note = detected_string
        else:
            self.previous_note = None

        return detected_string

    # ---------------------------------------------------------
    # 3. TABLA RENDER & TRIGGER
    # ---------------------------------------------------------
    def _draw_and_play_tabla(self, frame, w, h, fingertip):
        center_x = w // 2
        center_y = h // 2
        radius = min(w, h) // 3

        # Outer drum rim
        cv2.ellipse(frame, (center_x, center_y), (int(radius * 1.35), radius), 0, 0, 360, (200, 215, 220), -1)
        cv2.ellipse(frame, (center_x, center_y), (int(radius * 1.35), radius), 0, 0, 360, (40, 60, 65), 4)

        # Inner Maidan circle
        cv2.circle(frame, (center_x, center_y), int(radius * 0.8), (160, 185, 195), 3)

        # Center Black Syahi
        syahi_radius = int(radius * 0.36)
        cv2.circle(frame, (center_x, center_y), syahi_radius, (35, 40, 45), -1)
        cv2.circle(frame, (center_x, center_y), syahi_radius, (20, 25, 30), 2)

        # Labels
        cv2.putText(frame, "DHA (Center)", (center_x - 55, center_y + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (230, 240, 245), 2)
        cv2.putText(frame, "TIN (Top)", (center_x - 42, center_y - int(radius * 0.5)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 50, 55), 2)
        cv2.putText(frame, "DHI (Left)", (center_x - int(radius * 0.95), center_y + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 50, 55), 2)
        cv2.putText(frame, "NA (Right)", (center_x + int(radius * 0.55), center_y + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 50, 55), 2)

        detected_zone = None
        if fingertip:
            fx, fy = fingertip
            dist = np.sqrt((fx - center_x) ** 2 + (fy - center_y) ** 2)
            if dist < radius * 1.2:
                if dist < syahi_radius:
                    detected_zone = "DHA"
                elif fy < center_y - syahi_radius:
                    detected_zone = "TIN"
                elif fx < center_x:
                    detected_zone = "DHI"
                else:
                    detected_zone = "NA"

                # Visual pulse around hit point
                cv2.circle(frame, (fx, fy), 24, (100, 240, 255), 3)

        if detected_zone is not None:
            if detected_zone != self.previous_note:
                self._play_sound("TABLA", detected_zone)
                self.previous_note = detected_zone
        else:
            self.previous_note = None

        return detected_zone
