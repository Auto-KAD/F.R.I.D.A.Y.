from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
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
import speech_recognition as sr
import pyttsx3
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

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

class GeminiWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            if not api_key:
                self.error_occurred.emit("GEMINI_API_KEY not found. Please add it to your .env file.")
                return
                
            if not client:
                self.error_occurred.emit("Gemini client not initialized.")
                return

            now = time.time()
            last_error = None
            
            for model_name in _MODEL_LADDER:
                # Skip models that are cooling down
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
                    self.response_ready.emit(response.text)
                    return
                except Exception as e:
                    last_error = e
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
                        self.error_occurred.emit(f"API Error: {err_str}")
                        return

            self.error_occurred.emit(
                "All Gemini models are currently overloaded. Please try again in a minute."
            )
        except Exception as e:
            self.error_occurred.emit(f"Unexpected Error: {str(e)}")


class VoiceWorker(QThread):
    """Listens to microphone and emits recognized text."""
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()

    def run(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                self.listening_started.emit()
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)

            text = recognizer.recognize_google(audio)
            self.text_recognized.emit(text)
        except sr.WaitTimeoutError:
            self.error_occurred.emit("No speech detected. Try again.")
        except sr.UnknownValueError:
            self.error_occurred.emit("Could not understand. Try again.")
        except sr.RequestError as e:
            self.error_occurred.emit(f"Speech service error: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Mic error: {e}")


class TTSWorker(QThread):
    """Speaks text using pyttsx3 in background."""
    finished = pyqtSignal()

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 185)
            voices = engine.getProperty('voices')
            # Try to pick a female voice for FRIDAY
            for voice in voices:
                if 'female' in voice.name.lower() or 'samantha' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.say(self.text)
            engine.runAndWait()
            engine.stop()
        except Exception:
            pass
        finally:
            self.finished.emit()

class ChatbotPanel(QFrame):

    close_requested = pyqtSignal()

    def __init__(self, username):

        super().__init__()

        self.username = username
        self.is_listening = False
        self.tts_enabled = True

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

        # Mic button for voice input
        self.mic_button = QPushButton("🎙")

        self.mic_button.setFixedSize(
            42,
            42
        )

        self.mic_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.mic_button.clicked.connect(
            self.toggle_voice_input
        )

        input_layout.addWidget(
            self.input_box
        )

        input_layout.addWidget(
            self.mic_button
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

            QPushButton#micListening {
                background-color: #3d1a1a;
                border: 1px solid #ff4444;
                color: #ff4444;
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
            f"FRIDAY: Thinking..."
        )

        self.input_box.clear()
        
        # Disable input while waiting for response
        self.input_box.setEnabled(False)

        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
        
        # Start Gemini worker thread
        self.worker = GeminiWorker(message)
        self.worker.response_ready.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def handle_response(self, response_text):
        # Remove the 'Thinking...' line
        text = self.chat_area.toPlainText()
        lines = text.split('\n')
        if lines and lines[-1] == "FRIDAY: Thinking...":
            lines.pop()
            self.chat_area.setText('\n'.join(lines))
            
        self.chat_area.append(
            f"\nFRIDAY: {response_text}"
        )
        self.input_box.setEnabled(True)
        self.input_box.setFocus()
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

        # Speak the response
        if self.tts_enabled:
            self.tts_worker = TTSWorker(response_text)
            self.tts_worker.start()

    def handle_error(self, error_msg):
        # Remove the 'Thinking...' line
        text = self.chat_area.toPlainText()
        lines = text.split('\n')
        if lines and lines[-1] == "FRIDAY: Thinking...":
            lines.pop()
            self.chat_area.setText('\n'.join(lines))
            
        self.chat_area.append(
            f"\nFRIDAY (Error): {error_msg}"
        )
        self.input_box.setEnabled(True)
        self.input_box.setFocus()
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

    # ======================================================
    # VOICE INPUT
    # ======================================================

    def toggle_voice_input(self):
        if self.is_listening:
            return

        self.is_listening = True
        self.mic_button.setObjectName("micListening")
        self.mic_button.setStyleSheet(self.mic_button.styleSheet())  # force refresh
        self.mic_button.setText("●")
        self.input_box.setPlaceholderText("Listening...")

        self.voice_worker = VoiceWorker()
        self.voice_worker.text_recognized.connect(self.on_voice_recognized)
        self.voice_worker.error_occurred.connect(self.on_voice_error)
        self.voice_worker.start()

    def on_voice_recognized(self, text):
        self.reset_mic_button()
        self.input_box.setText(text)
        self.send_message()

    def on_voice_error(self, error):
        self.reset_mic_button()
        self.chat_area.append(f"\nFRIDAY: {error}")
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

    def reset_mic_button(self):
        self.is_listening = False
        self.mic_button.setObjectName("")
        self.mic_button.setText("🎙")
        self.input_box.setPlaceholderText("Ask FRIDAY...")
        # Reapply parent stylesheet
        self.setStyleSheet(self.styleSheet())