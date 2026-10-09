from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QSizePolicy
)
import speech_recognition as sr
import pyttsx3
import os
import sys
import re
import subprocess
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from dashboard.theme import apply_cloud_garden_theme

# Try to load .env from .venv or root
load_dotenv(".venv/.env")
load_dotenv(".env")

# Initialize Gemini client with explicit timeout
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30000)
    )
else:
    client = None

# Model fallback ladder (stable models first, newest last)
_MODEL_LADDER = [
    'gemini-3.5-flash',
    'gemini-3.6-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.1-flash-lite',
    'gemini-3.8-flash',
]

# Track which models are temporarily down
_model_cooldowns = {}
_COOLDOWN_503 = 60       # Rest for 1 min on 503
_COOLDOWN_404 = 3600     # Skip for 1 hour on 404


def clean_text_for_speech(text):
    """Strip markdown formatting for natural, clean spoken audio."""
    if not text:
        return ""
    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Inline code
    text = re.sub(r"`([^`]+)`", r"\g<1>", text)
    # Markdown links
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\g<1>", text)
    # Headers
    text = re.sub(r"#+\s*", "", text)
    # Bold / italic markers
    text = re.sub(r"[*_~]", "", text)
    # Bullet markers at start of line
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    # Collapse extra whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_stop_thread(thread, timeout_ms=300):
    """Safely and synchronously stops a QThread without destroying it while running."""
    if thread is None:
        return
    if thread.isRunning():
        if hasattr(thread, "stop"):
            thread.stop()
        elif hasattr(thread, "cancel"):
            thread.cancel()
        else:
            thread.quit()

        if not thread.wait(timeout_ms):
            thread.terminate()
            thread.wait()


class GeminiWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True
        self.quit()

    def run(self):
        try:
            if self._is_cancelled:
                return

            if not api_key:
                self.error_occurred.emit("GEMINI_API_KEY not found. Please add it to your .env file.")
                return

            if not client:
                self.error_occurred.emit("Gemini client not initialized.")
                return

            now = time.time()

            for model_name in _MODEL_LADDER:
                if self._is_cancelled:
                    return

                if model_name in _model_cooldowns:
                    if now < _model_cooldowns[model_name]:
                        continue
                    else:
                        del _model_cooldowns[model_name]

                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=self.prompt
                    )
                    if not self._is_cancelled:
                        self.response_ready.emit(response.text)
                    return
                except Exception as e:
                    err_str = str(e)
                    if "503" in err_str or "UNAVAILABLE" in err_str:
                        _model_cooldowns[model_name] = now + _COOLDOWN_503
                        continue
                    elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        _model_cooldowns[model_name] = now + _COOLDOWN_503
                        continue
                    elif "404" in err_str or "NOT_FOUND" in err_str:
                        _model_cooldowns[model_name] = now + _COOLDOWN_404
                        continue
                    else:
                        if not self._is_cancelled:
                            self.error_occurred.emit(f"API Error: {err_str}")
                        return

            if not self._is_cancelled:
                self.error_occurred.emit(
                    "All Gemini models are currently overloaded. Please try again in a minute."
                )
        except Exception as e:
            if not self._is_cancelled:
                self.error_occurred.emit(f"Unexpected Error: {str(e)}")


class VoiceWorker(QThread):
    """Listens to microphone and emits recognized text."""
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._is_stopped = False

    def stop(self):
        self._is_stopped = True
        self.quit()

    def run(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8

        try:
            with sr.Microphone() as source:
                if self._is_stopped:
                    return
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                if self._is_stopped:
                    return
                self.listening_started.emit()
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)

            if self._is_stopped:
                return

            text = recognizer.recognize_google(audio)
            if not self._is_stopped:
                self.text_recognized.emit(text)
        except sr.WaitTimeoutError:
            if not self._is_stopped:
                self.error_occurred.emit("No speech detected.")
        except sr.UnknownValueError:
            if not self._is_stopped:
                self.error_occurred.emit("Could not understand.")
        except sr.RequestError as e:
            if not self._is_stopped:
                self.error_occurred.emit(f"Speech service error: {e}")
        except Exception as e:
            if not self._is_stopped:
                self.error_occurred.emit(f"Mic error: {e}")


class TTSWorker(QThread):
    """Speaks text in background with INSTANT interrupt/kill capability."""
    finished = pyqtSignal()

    def __init__(self, text):
        super().__init__()
        self.text = clean_text_for_speech(text)
        self.process = None
        self.engine = None
        self._is_stopped = False

    def stop(self):
        """Immediately terminates audio playback with 0ms delay."""
        self._is_stopped = True

        # If on macOS and using 'say' subprocess:
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.kill()
            except Exception:
                pass

        if sys.platform == "darwin":
            try:
                os.system("killall say 2>/dev/null")
            except Exception:
                pass

        # If using pyttsx3 fallback:
        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass

        self.quit()

    def run(self):
        try:
            if not self.text or self._is_stopped:
                return

            if sys.platform == "darwin":
                # On macOS, native 'say' with Samantha voice can be killed instantly
                cmd = ["say", "-r", "190", "-v", "Samantha", self.text]
                self.process = subprocess.Popen(cmd)
                self.process.wait()
            else:
                # Windows / Linux pyttsx3
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 185)
                voices = self.engine.getProperty("voices")
                for voice in voices:
                    if "female" in voice.name.lower():
                        self.engine.setProperty("voice", voice.id)
                        break
                if not self._is_stopped:
                    self.engine.say(self.text)
                    self.engine.runAndWait()
        except Exception:
            pass
        finally:
            self.process = None
            if not self._is_stopped:
                self.finished.emit()


class ChatbotPanel(QFrame):

    close_requested = pyqtSignal()

    def __init__(self, username):
        super().__init__()

        self.username = username
        self.is_listening = False
        self.is_speaking = False
        self.is_generating = False
        self.tts_enabled = True

        self.worker = None        # GeminiWorker
        self.voice_worker = None  # VoiceWorker
        self.tts_worker = None    # TTSWorker

        self.setObjectName("chatbotPanel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(12)

        # ==================================================
        # HEADER
        # ==================================================
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)

        title = QLabel("FRIDAY")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("AI ASSISTANT")
        sub_font = QFont()
        sub_font.setPointSize(9)
        subtitle.setFont(sub_font)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Mute / Unmute narration toggle
        self.tts_toggle_btn = QPushButton("🔊")
        self.tts_toggle_btn.setObjectName("ttsToggleBtn")
        self.tts_toggle_btn.setFixedSize(42, 42)
        self.tts_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tts_toggle_btn.setToolTip("Voice narration is ON (click to mute)")
        self.tts_toggle_btn.clicked.connect(self.toggle_narration)
        header_layout.addWidget(self.tts_toggle_btn)

        # Close button
        close_button = QPushButton("×")
        close_button.setFixedSize(42, 42)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.on_close_clicked)
        header_layout.addWidget(close_button)

        main_layout.addLayout(header_layout)

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
        main_layout.addWidget(self.chat_area, 1)

        # ==================================================
        # PROMINENT STOP NARRATION / STATUS BAR
        # ==================================================
        self.status_bar = QFrame()
        self.status_bar.setObjectName("statusBar")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(12, 6, 12, 6)
        status_layout.setSpacing(8)

        self.status_label = QLabel("🔊 FRIDAY is speaking...")
        self.status_label.setObjectName("statusLabel")

        self.stop_narration_btn = QPushButton("⏹ STOP NARRATION")
        self.stop_narration_btn.setObjectName("stopNarrationBtn")
        self.stop_narration_btn.setFixedHeight(38)
        self.stop_narration_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_narration_btn.clicked.connect(self.stop_current_action)

        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.stop_narration_btn)
        self.status_bar.setLayout(status_layout)
        self.status_bar.hide()

        main_layout.addWidget(self.status_bar)

        # ==================================================
        # INPUT AREA
        # ==================================================
        input_layout = QHBoxLayout()

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask FRIDAY...")
        self.input_box.returnPressed.connect(self.handle_input_return)

        # Voice input button
        self.mic_button = QPushButton("🎙")
        self.mic_button.setObjectName("micButton")
        self.mic_button.setFixedSize(50, 50)
        self.mic_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_button.setToolTip("Voice input")
        self.mic_button.clicked.connect(self.toggle_voice_input)

        # Send / Stop action button
        self.action_button = QPushButton("➤")
        self.action_button.setObjectName("actionButton")
        self.action_button.setFixedSize(50, 50)
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.setToolTip("Send message")
        self.action_button.clicked.connect(self.on_action_button_clicked)

        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.mic_button)
        input_layout.addWidget(self.action_button)

        main_layout.addLayout(input_layout)
        self.setLayout(main_layout)

        # ==================================================
        # STYLESHEET
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
                font-size: 11px;
            }

            QLineEdit {
                background-color: #0b0f14;
                color: #ffffff;
                border: 1px solid #394656;
                border-radius: 12px;
                padding: 10px;
                font-size: 11px;
            }

            QLineEdit:focus {
                border: 1px solid #6d8097;
            }

            QLineEdit:disabled {
                background-color: #0d1218;
                color: #7b8a99;
                border: 1px solid #222b37;
            }

            QPushButton {
                background-color: #1b2430;
                color: #e8f0ff;
                border: 1px solid #323d4c;
                border-radius: 10px;
                font-size: 12px;
            }

            QPushButton:hover {
                background-color: #273342;
                border: 1px solid #566579;
            }

            QPushButton:pressed {
                background-color: #303d4d;
            }

            QPushButton:disabled {
                background-color: #121820;
                border: 1px solid #1f2732;
                color: #435265;
            }

            /* Stop Button */
            QPushButton#actionStop {
                background-color: #8c2020;
                border: 1px solid #ff4d4d;
                color: #ffffff;
                font-size: 14px;
            }

            QPushButton#actionStop:hover {
                background-color: #ab2828;
                border: 1px solid #ff7070;
            }

            /* Mic Active/Listening */
            QPushButton#micListening {
                background-color: #8c2020;
                border: 1px solid #ff4d4d;
                color: #ffffff;
            }

            QPushButton#micListening:hover {
                background-color: #ab2828;
            }

            /* Narration / Status Banner */
            QFrame#statusBar {
                background-color: #261111;
                border: 1px solid #e53935;
                border-radius: 10px;
            }

            QLabel#statusLabel {
                color: #ffcdd2;
                font-size: 11px;
                font-weight: 600;
            }

            QPushButton#stopNarrationBtn {
                background-color: #b71c1c;
                border: 1px solid #ff5252;
                color: #ffffff;
                border-radius: 6px;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 10px;
            }

            QPushButton#stopNarrationBtn:hover {
                background-color: #d32f2f;
                border: 1px solid #ff7979;
            }

            QPushButton#stopNarrationBtn:pressed {
                background-color: #8b1010;
            }

            QPushButton#ttsToggleBtn {
                background-color: #1b2430;
                border: 1px solid #323d4c;
                border-radius: 8px;
                font-size: 13px;
            }

            QPushButton#ttsToggleBtn:hover {
                background-color: #273342;
                border: 1px solid #566579;
            }
        """)
        apply_cloud_garden_theme(self, """
            QFrame#chatbotPanel { background-color: #F5F3E9; border-left: 2px solid #CBDCCF; }
            QFrame#statusBar { background-color: #F5E9E6; border-color: #E4C6BE; }
            QLabel#statusLabel { color: #805C55; }
            QPushButton#stopNarrationBtn { background-color: #EEDBD5; color: #704D48; border-color: #DDBEB5; }
            QPushButton#actionStop, QPushButton#micListening { background-color: #EEDBD5; color: #704D48; border-color: #DDBEB5; }
        """)

    # ======================================================
    # NARRATION TOGGLE
    # ======================================================

    def toggle_narration(self):
        """Toggles audio narration ON/OFF."""
        self.tts_enabled = not self.tts_enabled
        if not self.tts_enabled:
            self.stop_speaking()
            self.tts_toggle_btn.setText("🔇")
            self.tts_toggle_btn.setToolTip("Voice narration is OFF (click to enable)")
        else:
            self.tts_toggle_btn.setText("🔊")
            self.tts_toggle_btn.setToolTip("Voice narration is ON (click to mute)")

    # ======================================================
    # ACTION HANDLERS
    # ======================================================

    def on_action_button_clicked(self):
        """Action button acts as Stop when generating or speaking, and Send otherwise."""
        if self.is_generating or self.is_speaking:
            self.stop_current_action()
        else:
            self.send_message()

    def handle_input_return(self):
        """When user presses Enter: if speaking, halt speech and send new message immediately."""
        if self.is_speaking:
            self.stop_speaking()
        self.send_message()

    def stop_current_action(self):
        """Universal stop button behavior."""
        if self.is_speaking:
            self.stop_speaking()
        elif self.is_generating:
            self.stop_generation()
        elif self.is_listening:
            self.stop_listening()
        else:
            self.update_ui_state()

    def stop_all(self):
        """Stop all workers (speaking, listening, and generation)."""
        self.stop_listening()
        self.stop_speaking()
        self.stop_generation()

    def on_close_clicked(self):
        self.stop_all()
        self.close_requested.emit()

    def hideEvent(self, event):
        self.stop_all()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.stop_all()
        super().closeEvent(event)

    # ======================================================
    # SEND MESSAGE
    # ======================================================

    def send_message(self):
        message = self.input_box.text().strip()

        if not message:
            return

        # Interrupt any speech or listening before initiating new request
        if self.is_speaking:
            self.stop_speaking()
        if self.is_listening:
            self.stop_listening()

        self.chat_area.append(f"\nYOU: {message}")
        self.chat_area.append("FRIDAY: Thinking...")

        self.input_box.clear()
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

        self.is_generating = True
        self.update_ui_state()

        # Stop old worker safely if still alive
        if self.worker is not None and self.worker.isRunning():
            safe_stop_thread(self.worker)

        # Start Gemini worker thread
        self.worker = GeminiWorker(message)
        self.worker.response_ready.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def stop_generation(self):
        self.is_generating = False
        if self.worker is not None:
            safe_stop_thread(self.worker)
            self.worker = None

        text = self.chat_area.toPlainText()
        lines = text.split('\n')
        if lines and lines[-1] == "FRIDAY: Thinking...":
            lines.pop()
            self.chat_area.setText('\n'.join(lines))

        self.chat_area.append("\nFRIDAY: [Response stopped]")
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

        self.update_ui_state()

    def handle_response(self, response_text):
        self.is_generating = False

        # Remove the 'Thinking...' line
        text = self.chat_area.toPlainText()
        lines = text.split('\n')
        if lines and lines[-1] == "FRIDAY: Thinking...":
            lines.pop()
            self.chat_area.setText('\n'.join(lines))

        self.chat_area.append(f"\nFRIDAY: {response_text}")
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

        # Speak the response if narration is enabled
        if self.tts_enabled:
            self.start_speaking(response_text)
        else:
            self.update_ui_state()

    def handle_error(self, error_msg):
        self.is_generating = False

        # Remove the 'Thinking...' line
        text = self.chat_area.toPlainText()
        lines = text.split('\n')
        if lines and lines[-1] == "FRIDAY: Thinking...":
            lines.pop()
            self.chat_area.setText('\n'.join(lines))

        self.chat_area.append(f"\nFRIDAY (Error): {error_msg}")
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
        self.update_ui_state()

    # ======================================================
    # TEXT TO SPEECH (NARRATION OUTPUT)
    # ======================================================

    def start_speaking(self, text):
        """Initiates voice narration and updates UI with Stop Narration button."""
        # Stop any active voice listening to prevent echoing speaker audio
        if self.is_listening:
            self.stop_listening()

        # Stop previous TTS worker if still alive
        if self.tts_worker is not None and self.tts_worker.isRunning():
            safe_stop_thread(self.tts_worker)

        self.is_speaking = True
        self.update_ui_state()

        self.tts_worker = TTSWorker(text)
        self.tts_worker.finished.connect(self.on_tts_finished)
        self.tts_worker.start()

    def stop_speaking(self):
        """Immediately halts and kills narration audio output."""
        self.is_speaking = False
        if self.tts_worker is not None:
            safe_stop_thread(self.tts_worker)
            self.tts_worker = None

        if sys.platform == "darwin":
            os.system("killall say 2>/dev/null")

        self.update_ui_state()

    def on_tts_finished(self):
        self.is_speaking = False
        self.update_ui_state()

    # ======================================================
    # VOICE INPUT (STT)
    # ======================================================

    def toggle_voice_input(self):
        # If bot is currently speaking, clicking mic halts speech immediately
        if self.is_speaking:
            self.stop_speaking()

        # If already listening, clicking again cancels/stops listening
        if self.is_listening:
            self.stop_listening()
            return

        self.is_listening = True
        self.update_ui_state()

        if self.voice_worker is not None and self.voice_worker.isRunning():
            safe_stop_thread(self.voice_worker)

        self.voice_worker = VoiceWorker()
        self.voice_worker.text_recognized.connect(self.on_voice_recognized)
        self.voice_worker.error_occurred.connect(self.on_voice_error)
        self.voice_worker.start()

    def stop_listening(self):
        self.is_listening = False
        if self.voice_worker is not None:
            safe_stop_thread(self.voice_worker)
            self.voice_worker = None
        self.update_ui_state()

    def on_voice_recognized(self, text):
        self.is_listening = False
        self.update_ui_state()
        self.input_box.setText(text)
        self.send_message()

    def on_voice_error(self, error):
        self.is_listening = False
        self.update_ui_state()
        self.chat_area.append(f"\nFRIDAY: {error}")
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

    # ======================================================
    # UI STATE MACHINE
    # ======================================================

    def update_ui_state(self):
        """Synchronizes UI elements according to current state."""
        if self.is_speaking:
            # Bot is narrating via TTS
            self.input_box.setEnabled(True)
            self.input_box.setPlaceholderText("Type message or click Stop Narration...")

            # CRITICAL: Mic disabled while bot speaks to prevent listening to itself
            self.mic_button.setEnabled(False)
            self.mic_button.setObjectName("micDisabled")
            self.mic_button.setText("🎙")
            self.mic_button.setToolTip("Microphone muted while FRIDAY is speaking")

            # Action button becomes Stop button
            self.action_button.setEnabled(True)
            self.action_button.setObjectName("actionStop")
            self.action_button.setText("⏹")
            self.action_button.setToolTip("Stop narration")

            # Prominent Red Stop Narration Banner
            self.status_label.setText("🔊 FRIDAY is narrating...")
            self.stop_narration_btn.setText("⏹ STOP NARRATION")
            self.status_bar.show()

        elif self.is_generating:
            # Bot is querying Gemini API
            self.input_box.setEnabled(False)
            self.input_box.setPlaceholderText("FRIDAY is thinking...")

            self.mic_button.setEnabled(False)
            self.mic_button.setObjectName("micDisabled")
            self.mic_button.setText("🎙")
            self.mic_button.setToolTip("Microphone unavailable while thinking")

            self.action_button.setEnabled(True)
            self.action_button.setObjectName("actionStop")
            self.action_button.setText("⏹")
            self.action_button.setToolTip("Stop generating")

            self.status_label.setText("● FRIDAY is thinking...")
            self.stop_narration_btn.setText("⏹ Stop")
            self.status_bar.show()

        elif self.is_listening:
            # User is speaking into mic
            self.input_box.setEnabled(False)
            self.input_box.setPlaceholderText("Listening... (click ⏹ to cancel)")

            self.mic_button.setEnabled(True)
            self.mic_button.setObjectName("micListening")
            self.mic_button.setText("⏹")
            self.mic_button.setToolTip("Stop listening")

            self.action_button.setEnabled(False)
            self.action_button.setObjectName("actionButton")
            self.action_button.setText("➤")
            self.action_button.setToolTip("Send")

            self.status_label.setText("🎙 Listening to voice...")
            self.stop_narration_btn.setText("⏹ Cancel")
            self.status_bar.show()

        else:
            # Idle ready state
            self.input_box.setEnabled(True)
            self.input_box.setPlaceholderText("Ask FRIDAY...")

            self.mic_button.setEnabled(True)
            self.mic_button.setObjectName("micButton")
            self.mic_button.setText("🎙")
            self.mic_button.setToolTip("Voice input")

            self.action_button.setEnabled(True)
            self.action_button.setObjectName("actionButton")
            self.action_button.setText("➤")
            self.action_button.setToolTip("Send message")

            # Hide narration banner
            self.status_bar.hide()

        # Refresh stylesheet dynamically for changed object names
        self.setStyleSheet(self.styleSheet())
        if not self.is_generating and not self.is_listening:
            self.input_box.setFocus()