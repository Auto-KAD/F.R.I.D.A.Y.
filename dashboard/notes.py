import json
import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QListWidget,
    QLineEdit,
    QPlainTextEdit
)

from dashboard.theme import apply_cloud_garden_theme


class NotesPanel(QWidget):
    return_home_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.notes_file = os.path.join("data", "notes.json")
        self.notes = []
        self.current_index = -1
        self.setup_ui()
        self.load_notes()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("NOTES")
        title.setFont(QFont("Georgia", 24, QFont.Weight.Bold))
        subtitle = QLabel("A quiet place to collect your thoughts.")
        header_text = QVBoxLayout()
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text)
        header.addStretch()

        self.new_button = QPushButton("＋  New note")
        self.new_button.clicked.connect(self.new_note)
        header.addWidget(self.new_button)
        self.save_button = QPushButton("Save note")
        self.save_button.clicked.connect(self.save_note)
        header.addWidget(self.save_button)
        layout.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(14)

        list_frame = QFrame()
        list_frame.setObjectName("notesListFrame")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(12, 12, 12, 12)
        list_title = QLabel("YOUR NOTES")
        list_title.setObjectName("eyebrow")
        list_layout.addWidget(list_title)
        self.note_list = QListWidget()
        self.note_list.currentRowChanged.connect(self.select_note)
        list_layout.addWidget(self.note_list, 1)
        self.delete_button = QPushButton("Delete selected")
        self.delete_button.clicked.connect(self.delete_note)
        list_layout.addWidget(self.delete_button)
        content.addWidget(list_frame, 1)

        editor_frame = QFrame()
        editor_frame.setObjectName("noteEditorFrame")
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(18, 16, 18, 16)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Untitled note")
        self.title_edit.setFont(QFont("Georgia", 19, QFont.Weight.Bold))
        editor_layout.addWidget(self.title_edit)
        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText("Start writing...")
        editor_layout.addWidget(self.body_edit, 1)
        self.status_label = QLabel("Notes save on this device.")
        self.status_label.setObjectName("mutedText")
        editor_layout.addWidget(self.status_label)
        content.addWidget(editor_frame, 3)
        layout.addLayout(content, 1)

        apply_cloud_garden_theme(self, """
            QFrame#notesListFrame, QFrame#noteEditorFrame { background-color: rgba(255, 253, 246, 238); }
            QLabel#eyebrow { color: #64856E; font-weight: bold; }
            QLabel#mutedText { color: #71877A; }
        """)

    def load_notes(self):
        try:
            with open(self.notes_file, "r", encoding="utf-8") as notes_file:
                loaded_notes = json.load(notes_file)
            if isinstance(loaded_notes, list):
                self.notes = [
                    {"title": str(note.get("title", "")), "body": str(note.get("body", ""))}
                    for note in loaded_notes
                    if isinstance(note, dict)
                ]
        except (OSError, json.JSONDecodeError):
            self.notes = []

        self.note_list.clear()
        for note in self.notes:
            self.note_list.addItem(note["title"] or "Untitled note")
        if self.notes:
            self.note_list.setCurrentRow(0)
        else:
            self.title_edit.clear()
            self.body_edit.clear()

    def select_note(self, index):
        if (
            self.current_index >= 0
            and self.current_index != index
            and self.current_index < len(self.notes)
        ):
            self._update_current_note()

        if index < 0 or index >= len(self.notes):
            self.current_index = -1
            return

        self.current_index = index
        note = self.notes[index]
        self.title_edit.setText(note["title"])
        self.body_edit.setPlainText(note["body"])
        self.status_label.setText("Saved note")

    def _update_current_note(self):
        title = self.title_edit.text().strip() or "Untitled note"
        body = self.body_edit.toPlainText()
        if self.current_index < 0:
            self.notes.append({"title": title, "body": body})
            self.current_index = len(self.notes) - 1
            self.note_list.addItem(title)
            self.note_list.setCurrentRow(self.current_index)
        else:
            self.notes[self.current_index] = {"title": title, "body": body}
            self.note_list.item(self.current_index).setText(title)

    def save_note(self):
        self._update_current_note()
        os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)
        with open(self.notes_file, "w", encoding="utf-8") as notes_file:
            json.dump(self.notes, notes_file, indent=2, ensure_ascii=False)
        self.status_label.setText("Saved")

    def new_note(self):
        if self.current_index >= 0:
            self._update_current_note()
        self.notes.append({"title": "", "body": ""})
        self.current_index = len(self.notes) - 1
        self.note_list.addItem("Untitled note")
        self.note_list.setCurrentRow(self.current_index)
        self.title_edit.clear()
        self.body_edit.clear()
        self.title_edit.setFocus()

    def delete_note(self):
        if self.current_index < 0:
            return
        deleted_index = self.current_index
        self.notes.pop(deleted_index)
        self.note_list.takeItem(deleted_index)
        os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)
        with open(self.notes_file, "w", encoding="utf-8") as notes_file:
            json.dump(self.notes, notes_file, indent=2, ensure_ascii=False)
        self.current_index = -1
        if self.notes:
            next_index = min(deleted_index, len(self.notes) - 1)
            self.note_list.setCurrentRow(next_index)
            self.select_note(next_index)
        else:
            self.title_edit.clear()
            self.body_edit.clear()
        self.status_label.setText("Note deleted")