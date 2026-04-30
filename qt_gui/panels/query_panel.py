"""Query Panel - Input and controls for agent queries."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFrame


class QueryPanel(QWidget):
    """Panel containing query input and control buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Callback slots (to be connected by SessionTab)
        self.on_run = None
        self.on_pause = None

        self.init_ui()
        self.setup_signal_connections()

    def init_ui(self):
        """Initialize the query panel UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Query input frame
        query_frame = QFrame()
        query_frame.setFrameStyle(QFrame.Shape.Box)
        query_layout = QVBoxLayout()
        query_frame.setLayout(query_layout)

        query_layout.addWidget(QLabel("Query:"))
        self.query_entry = QTextEdit()
        self.query_entry.setMaximumHeight(100)
        self.query_entry.setPlaceholderText("Enter your query here...")
        query_layout.addWidget(self.query_entry)

        button_layout = QHBoxLayout()

        # Run button
        self.run_btn = QPushButton("RUN")
        self.run_btn.setMinimumWidth(80)
        button_layout.addWidget(self.run_btn)

        # Pause button
        self.pause_btn = QPushButton("PAUSE")
        self.pause_btn.setMinimumWidth(80)
        button_layout.addWidget(self.pause_btn)

        button_layout.addStretch()

        query_layout.addLayout(button_layout)
        layout.addWidget(query_frame)

    def setup_signal_connections(self):
        """Connect button signals to callbacks."""
        self.run_btn.clicked.connect(self._on_run_clicked)
        self.pause_btn.clicked.connect(self._on_pause_clicked)

    def _on_run_clicked(self):
        """Handle run button click."""
        if self.on_run:
            self.on_run()

    def _on_pause_clicked(self):
        """Handle pause button click."""
        if self.on_pause:
            self.on_pause()

    def get_query_text(self):
        """Get the current query text."""
        return self.query_entry.toPlainText().strip()

    def clear_query(self):
        """Clear the query input."""
        self.query_entry.clear()

    def set_run_enabled(self, enabled):
        """Enable/disable run button."""
        self.run_btn.setEnabled(enabled)

    def set_pause_enabled(self, enabled):
        """Enable/disable pause button."""
        self.pause_btn.setEnabled(enabled)

    def set_buttons_running(self):
        """Set buttons for running state."""
        self.run_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)

    def set_buttons_paused(self):
        """Set buttons for paused state."""
        self.run_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def set_buttons_idle(self):
        """Set buttons for idle state."""
        self.run_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def set_focus_to_query(self):
        """Set focus to query entry."""
        self.query_entry.setFocus()
