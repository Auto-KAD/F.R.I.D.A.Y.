CLOUD_GARDEN_STYLESHEET = """
    QWidget {
        background-color: #EDF3E8;
        color: #35565A;
        font-family: "Segoe UI";
        font-size: 11pt;
    }

    QLabel {
        background-color: transparent;
        color: #35565A;
        border: none;
    }

    QFrame#calendarFrame,
    QFrame#rightFrame,
    QFrame#toolFrame,
    QFrame#card,
    QFrame#detailsFrame,
    QFrame#cameraFrame,
    QFrame#controlsFrame,
    QFrame#infoFrame,
    QFrame#mediaFrame,
    QFrame#volumeFrame,
    QFrame#playlistFrame {
        background-color: rgba(255, 253, 246, 238);
        border: 1px solid #D7E2D8;
        border-radius: 14px;
    }

    QPushButton {
        background-color: #FBFCF6;
        color: #365D5E;
        border: 1px solid #D1DDD2;
        border-radius: 12px;
        min-height: 42px;
        padding: 9px 14px;
        font-size: 11pt;
    }

    QPushButton:hover {
        background-color: #E5F1E6;
        border-color: #9FC4AE;
    }

    QPushButton:pressed {
        background-color: #D6E8D9;
    }

    QPushButton:disabled {
        background-color: #E6ECE4;
        color: #8A9C8D;
        border-color: #D4DDD2;
    }

    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
    QTimeEdit,
    QComboBox,
    QListWidget {
        background-color: rgba(255, 255, 250, 238);
        color: #35565A;
        border: 1px solid #CCDCCE;
        border-radius: 10px;
        padding: 9px 11px;
        selection-background-color: #CFE4D4;
        selection-color: #2F5754;
    }

    QLineEdit:focus,
    QTextEdit:focus,
    QPlainTextEdit:focus,
    QTimeEdit:focus,
    QComboBox:focus {
        border: 2px solid #85B39A;
    }

    QComboBox::drop-down {
        border: none;
        width: 28px;
    }

    QTabWidget::pane {
        background-color: rgba(255, 253, 246, 238);
        border: 1px solid #D7E2D8;
        border-radius: 12px;
        top: -1px;
    }

    QTabBar::tab {
        background-color: #E4EDE1;
        color: #55736B;
        border: 1px solid #D3DFD3;
        border-top-left-radius: 9px;
        border-top-right-radius: 9px;
        min-height: 38px;
        padding: 7px 16px;
        margin-right: 3px;
    }

    QTabBar::tab:selected {
        background-color: #FBFCF6;
        color: #376D68;
        border-bottom-color: #FBFCF6;
        font-weight: bold;
    }

    QTabBar::tab:hover {
        background-color: #EEF5EC;
    }

    QCalendarWidget {
        background-color: #FBFCF6;
        color: #35565A;
    }

    QCalendarWidget QToolButton {
        background-color: #E6EFE4;
        border: 1px solid #D3DFD3;
        border-radius: 8px;
        min-height: 34px;
        padding: 4px 9px;
        font-weight: bold;
    }

    QCalendarWidget QAbstractItemView {
        background-color: #FBFCF6;
        color: #35565A;
        selection-background-color: #CFE4D4;
        selection-color: #2F5754;
        alternate-background-color: #EEF4E9;
        outline: none;
    }

    QScrollBar:vertical {
        background: #EAF0E6;
        width: 14px;
        margin: 2px;
        border-radius: 7px;
    }

    QScrollBar::handle:vertical {
        background: #AAC6B0;
        min-height: 28px;
        border-radius: 7px;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
    }
"""


def apply_cloud_garden_theme(widget, extra_stylesheet=""):
    widget.setStyleSheet(
        CLOUD_GARDEN_STYLESHEET + extra_stylesheet
    )