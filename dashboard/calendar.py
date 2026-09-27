import json
import os

from PyQt6.QtCore import (
    Qt,
    QDate
)

from PyQt6.QtGui import (
    QFont,
    QTextCharFormat
)

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QCalendarWidget,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QTimeEdit,
    QMessageBox
)


class Calendar(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "FRIDAY — Calendar"
        )

        self.setMinimumSize(
            1000,
            650
        )

        # --------------------------------
        # EVENT STORAGE
        # --------------------------------

        self.events_file = (
            "data/calendar_events.json"
        )

        self.events = {}

        self.selected_date = (
            QDate.currentDate()
        )

        self.load_events()

        self.setup_ui()

        self.update_event_list()

        self.highlight_event_dates()

    # ==================================================
    # MAIN UI
    # ==================================================

    def setup_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            30,
            25,
            30,
            25
        )

        main_layout.setSpacing(
            18
        )

        # --------------------------------
        # HEADER
        # --------------------------------

        header_layout = QHBoxLayout()

        title = QLabel(
            "CALENDAR"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                28,
                QFont.Weight.Bold
            )
        )

        subtitle = QLabel(
            "FRIDAY schedule and reminders"
        )

        subtitle.setFont(
            QFont(
                "Segoe UI",
                12
            )
        )

        header_layout.addWidget(
            title
        )

        header_layout.addSpacing(
            18
        )

        header_layout.addWidget(
            subtitle
        )

        header_layout.addStretch()

        self.today_button = QPushButton(
            "TODAY"
        )

        self.today_button.setFixedSize(
            90,
            38
        )

        self.today_button.clicked.connect(
            self.go_to_today
        )

        header_layout.addWidget(
            self.today_button
        )

        main_layout.addLayout(
            header_layout
        )

        # --------------------------------
        # CONTENT
        # --------------------------------

        content_layout = QHBoxLayout()

        content_layout.setSpacing(
            20
        )

        # ==============================================
        # CALENDAR SECTION
        # ==============================================

        calendar_frame = QFrame()

        calendar_frame.setObjectName(
            "calendarFrame"
        )

        calendar_layout = QVBoxLayout()

        calendar_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        self.calendar = QCalendarWidget()

        self.calendar.setGridVisible(
            True
        )

        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )

        self.calendar.setSelectedDate(
            self.selected_date
        )

        self.calendar.selectionChanged.connect(
            self.date_selected
        )

        calendar_layout.addWidget(
            self.calendar
        )

        calendar_frame.setLayout(
            calendar_layout
        )

        content_layout.addWidget(
            calendar_frame,
            2
        )

        # ==============================================
        # RIGHT SIDE
        # ==============================================

        right_frame = QFrame()

        right_frame.setObjectName(
            "rightFrame"
        )

        right_layout = QVBoxLayout()

        right_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        # --------------------------------
        # SELECTED DATE
        # --------------------------------

        self.date_label = QLabel()

        self.date_label.setFont(
            QFont(
                "Segoe UI",
                17,
                QFont.Weight.Bold
            )
        )

        self.date_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        right_layout.addWidget(
            self.date_label
        )

        right_layout.addSpacing(
            10
        )

        # --------------------------------
        # EVENTS
        # --------------------------------

        events_title = QLabel(
            "EVENTS"
        )

        events_title.setFont(
            QFont(
                "Segoe UI",
                12,
                QFont.Weight.Bold
            )
        )

        right_layout.addWidget(
            events_title
        )

        self.event_list = QListWidget()

        self.event_list.setMinimumHeight(
            180
        )

        right_layout.addWidget(
            self.event_list
        )

        # --------------------------------
        # EVENT TITLE
        # --------------------------------

        self.event_title = QLineEdit()

        self.event_title.setPlaceholderText(
            "Event title"
        )

        right_layout.addWidget(
            self.event_title
        )

        # --------------------------------
        # EVENT TIME
        # --------------------------------

        time_layout = QHBoxLayout()

        time_label = QLabel(
            "TIME"
        )

        self.event_time = QTimeEdit()

        self.event_time.setDisplayFormat(
            "HH:mm"
        )

        time_layout.addWidget(
            time_label
        )

        time_layout.addStretch()

        time_layout.addWidget(
            self.event_time
        )

        right_layout.addLayout(
            time_layout
        )

        # --------------------------------
        # EVENT NOTES
        # --------------------------------

        self.event_notes = QTextEdit()

        self.event_notes.setPlaceholderText(
            "Notes / description"
        )

        self.event_notes.setMaximumHeight(
            90
        )

        right_layout.addWidget(
            self.event_notes
        )

        # --------------------------------
        # ADD EVENT
        # --------------------------------

        add_button = QPushButton(
            "ADD EVENT"
        )

        add_button.setFixedHeight(
            42
        )

        add_button.clicked.connect(
            self.add_event
        )

        right_layout.addWidget(
            add_button
        )

        # --------------------------------
        # DELETE EVENT
        # --------------------------------

        delete_button = QPushButton(
            "DELETE SELECTED EVENT"
        )

        delete_button.setFixedHeight(
            38
        )

        delete_button.clicked.connect(
            self.delete_event
        )

        right_layout.addWidget(
            delete_button
        )

        right_frame.setLayout(
            right_layout
        )

        content_layout.addWidget(
            right_frame,
            1
        )

        main_layout.addLayout(
            content_layout,
            1
        )

        # --------------------------------
        # CLOSE
        # --------------------------------

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.setFixedHeight(
            42
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

        self.apply_style()

    # ==================================================
    # STYLE
    # ==================================================

    def apply_style(self):

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f14;
                color: #e8f0ff;
            }

            QLabel {
                background-color: transparent;
                color: #e8f0ff;
            }

            QFrame#calendarFrame {
                background-color: #111720;
                border: 1px solid #303a48;
                border-radius: 16px;
            }

            QFrame#rightFrame {
                background-color: #111720;
                border: 1px solid #303a48;
                border-radius: 16px;
            }

            QCalendarWidget {
                background-color: #111720;
                color: #e8f0ff;
            }

            QCalendarWidget QToolButton {
                color: #e8f0ff;
                background-color: #1b2430;
                border: none;
                border-radius: 8px;
                padding: 6px;
                font-family: "Segoe UI";
                font-size: 12px;
                font-weight: bold;
            }

            QCalendarWidget QToolButton:hover {
                background-color: #273342;
            }

            QCalendarWidget QSpinBox {
                color: #e8f0ff;
                background-color: #1b2430;
                border: 1px solid #303a48;
            }

            QCalendarWidget QAbstractItemView {
                background-color: #111720;
                color: #e8f0ff;
                selection-background-color: #3a4a5e;
                selection-color: white;
                alternate-background-color: #141b24;
                outline: none;
            }

            QLineEdit,
            QTextEdit,
            QTimeEdit {
                background-color: #0f151d;
                color: #ffffff;
                border: 1px solid #394656;
                border-radius: 9px;
                padding: 8px;
                font-family: "Segoe UI";
            }

            QLineEdit:focus,
            QTextEdit:focus,
            QTimeEdit:focus {
                border: 1px solid #6d8097;
            }

            QListWidget {
                background-color: #0f151d;
                color: #e8f0ff;
                border: 1px solid #303a48;
                border-radius: 9px;
                padding: 5px;
            }

            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #27313e;
            }

            QListWidget::item:selected {
                background-color: #273342;
            }

            QPushButton {
                background-color: #1b2430;
                color: #e8f0ff;
                border: 1px solid #323d4c;
                border-radius: 10px;
                font-family: "Segoe UI";
                font-size: 11px;
                padding: 7px;
            }

            QPushButton:hover {
                background-color: #273342;
                border: 1px solid #566579;
            }

            QPushButton:pressed {
                background-color: #303d4d;
            }
        """)

    # ==================================================
    # EVENT HANDLING
    # ==================================================

    def date_selected(self):

        self.selected_date = (
            self.calendar.selectedDate()
        )

        self.update_event_list()

    def update_event_list(self):

        date_string = (
            self.selected_date.toString(
                "yyyy-MM-dd"
            )
        )

        display_date = (
            self.selected_date.toString(
                "dddd, dd MMMM yyyy"
            )
        )

        self.date_label.setText(
            display_date
        )

        self.event_list.clear()

        events = self.events.get(
            date_string,
            []
        )

        if not events:

            item = QListWidgetItem(
                "No events scheduled"
            )

            item.setFlags(
                Qt.ItemFlag.NoItemFlags
            )

            self.event_list.addItem(
                item
            )

            return

        for event in events:

            title = event.get(
                "title",
                "Untitled"
            )

            event_time = event.get(
                "time",
                "--:--"
            )

            notes = event.get(
                "notes",
                ""
            )

            if notes:

                text = (
                    f"{event_time}  |  "
                    f"{title}\n"
                    f"{notes}"
                )

            else:

                text = (
                    f"{event_time}  |  "
                    f"{title}"
                )

            item = QListWidgetItem(
                text
            )

            self.event_list.addItem(
                item
            )

    # ==================================================
    # ADD EVENT
    # ==================================================

    def add_event(self):

        title = (
            self.event_title.text()
            .strip()
        )

        if not title:

            QMessageBox.warning(
                self,
                "FRIDAY Calendar",
                "Please enter an event title."
            )

            return

        date_string = (
            self.selected_date.toString(
                "yyyy-MM-dd"
            )
        )

        event = {
            "title": title,
            "time": self.event_time.time().toString(
                "HH:mm"
            ),
            "notes": (
                self.event_notes
                .toPlainText()
                .strip()
            )
        }

        if date_string not in self.events:

            self.events[date_string] = []

        self.events[date_string].append(
            event
        )

        self.save_events()

        self.event_title.clear()

        self.event_notes.clear()

        self.update_event_list()

        self.highlight_event_dates()

        QMessageBox.information(
            self,
            "FRIDAY Calendar",
            "Event added successfully."
        )

    # ==================================================
    # DELETE EVENT
    # ==================================================

    def delete_event(self):

        selected_item = (
            self.event_list.currentItem()
        )

        if selected_item is None:

            return

        row = (
            self.event_list.row(
                selected_item
            )
        )

        date_string = (
            self.selected_date.toString(
                "yyyy-MM-dd"
            )
        )

        events = self.events.get(
            date_string,
            []
        )

        if row < 0 or row >= len(events):

            return

        confirm = QMessageBox.question(
            self,
            "Delete Event",
            "Delete the selected event?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if (
            confirm
            != QMessageBox.StandardButton.Yes
        ):

            return

        events.pop(
            row
        )

        if not events:

            self.events.pop(
                date_string,
                None
            )

        self.save_events()

        self.update_event_list()

        self.highlight_event_dates()

    # ==================================================
    # TODAY
    # ==================================================

    def go_to_today(self):

        today = QDate.currentDate()

        self.calendar.setSelectedDate(
            today
        )

        self.calendar.setCurrentPage(
            today.year(),
            today.month()
        )

        self.selected_date = today

        self.update_event_list()

    # ==================================================
    # EVENT DATE HIGHLIGHTING
    # ==================================================

    def highlight_event_dates(self):

        # Reset formatting by recreating the calendar
        # date formatting for the visible month.

        for date_string in self.events:

            date = QDate.fromString(
                date_string,
                "yyyy-MM-dd"
            )

            if not date.isValid():

                continue

            if not self.events[date_string]:

                continue

            format = QTextCharFormat()

            format.setFontWeight(
                QFont.Weight.Bold
            )

            self.calendar.setDateTextFormat(
                date,
                format
            )

    # ==================================================
    # SAVE EVENTS
    # ==================================================

    def save_events(self):

        directory = os.path.dirname(
            self.events_file
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        try:

            with open(
                self.events_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    self.events,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

        except Exception as error:

            print(
                "Could not save calendar events:",
                error
            )

    # ==================================================
    # LOAD EVENTS
    # ==================================================

    def load_events(self):

        if not os.path.exists(
            self.events_file
        ):

            self.events = {}

            return

        try:

            with open(
                self.events_file,
                "r",
                encoding="utf-8"
            ) as file:

                self.events = json.load(
                    file
                )

        except Exception as error:

            print(
                "Could not load calendar events:",
                error
            )

            self.events = {}

    # ==================================================
    # CLOSE
    # ==================================================

    def closeEvent(
        self,
        event
    ):

        self.save_events()

        event.accept()