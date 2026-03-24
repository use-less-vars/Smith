"""Theme management for the GUI."""
from typing import Optional


# Theme definitions as QSS (Qt Style Sheets) strings
THEMES = {
    "light": "",  # Default Fusion style, no custom stylesheet

    "dark": """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #4c4c4c;
        }
        QPushButton:pressed {
            background-color: #2c2c2c;
        }
        QLabel {
            color: #ffffff;
        }
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 3px;
        }
        QCheckBox {
            color: #ffffff;
        }
        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 15px;
        }
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 7px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
    """,

    "high_contrast": """
        QWidget {
            background-color: #000000;
            color: #ffffff;
        }
        QGroupBox {
            border: 2px solid #ffffff;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #ffff00;
        }
        QPushButton {
            background-color: #000000;
            border: 2px solid #ffffff;
            border-radius: 3px;
            padding: 5px 10px;
            color: #ffffff;
        }
        QPushButton:hover {
            background-color: #222222;
        }
        QPushButton:pressed {
            background-color: #444444;
        }
        QLabel {
            color: #ffffff;
        }
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #000000;
            color: #ffffff;
            border: 2px solid #ffffff;
            padding: 3px;
        }
        QCheckBox {
            color: #ffffff;
        }
        QCheckBox::indicator {
            border: 2px solid #ffffff;
        }
        QScrollBar:vertical {
            background-color: #000000;
            width: 15px;
        }
        QScrollBar::handle:vertical {
            background-color: #ffffff;
            border-radius: 7px;
            min-height: 20px;
        }
    """
}


def apply_theme(widget, theme_name: str) -> bool:
    """
    Apply a theme to the given widget (typically a window or application).

    Args:
        widget: The QWidget (usually QApplication or QMainWindow) to style
        theme_name: Name of the theme ("light", "dark", or "high_contrast")

    Returns:
        True if theme was applied, False if theme name not found
    """
    if theme_name in THEMES:
        widget.setStyleSheet(THEMES[theme_name])
        return True
    else:
        return False


def get_available_themes():
    """Return list of available theme names."""
    return list(THEMES.keys())
