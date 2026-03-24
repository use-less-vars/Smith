"""Output Panel - Event display and output area for the agent."""
import html
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTextEdit, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextDocument, QTextCursor

# Import from other extracted modules
from qt_gui.panels.event_models import EventModel, EventFilterProxyModel, EventDelegate
from qt_gui.panels.markdown_renderer import MarkdownRenderer
from qt_gui.utils.constants import MAX_RESULT_LENGTH
from qt_gui.utils.smart_scrolling import SmartScroller



class OutputPanel(QWidget):
    """Panel containing event display, filtering, and query controls."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Event model
        self.event_model = EventModel()
        self.filter_proxy_model = EventFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.event_model)

        # Token tracking (mirrored from SessionTab)
        self.total_input = 0
        self.total_output = 0
        self.context_length = 0

        self.init_ui()
        self.setup_signal_connections()

    def init_ui(self):
        """Initialize the output panel UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Filter controls
        filter_widget = QWidget()
        filter_layout = QHBoxLayout()
        filter_widget.setLayout(filter_layout)

        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_lineedit = QLineEdit()
        self.filter_lineedit.setPlaceholderText("Search events...")
        filter_layout.addWidget(self.filter_lineedit, 1)  # Stretch

        filter_layout.addWidget(QLabel("Type:"))
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems([
            "all", "turn", "final", "user_query", "stopped",
            "system", "user_interaction_requested", "token_warning",
            "turn_warning", "paused", "max_turns", "error",
            "thread_finished"
        ])
        filter_layout.addWidget(self.filter_type_combo)

        layout.addWidget(filter_widget)

        # Output text area
        self.output_textedit = QTextEdit()
        self.output_textedit.setReadOnly(True)
        self.output_textedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.output_textedit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.output_textedit.setAcceptRichText(True)
        self.output_textedit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.output_textedit.setStyleSheet("""
            QTextEdit:focus {
                border: none;
                outline: none;
            }
            QTextEdit {
                selection-background-color: #3399ff;
                selection-color: white;
            }
        """)
        layout.addWidget(self.output_textedit, 4)  # Larger stretch factor

        # Initialize smart scrolling
        self.smart_scroller = SmartScroller(self.output_textedit)

    def setup_signal_connections(self):
        """Connect filter signals."""
        self.filter_lineedit.textChanged.connect(self._apply_filter)
        self.filter_type_combo.currentTextChanged.connect(self._apply_filter)

    def _format_event_html(self, event):
        """Convert event dictionary to HTML representation."""
        etype = event.get('type', 'unknown')
        detail_level = event.get('_detail_level', 'normal')

        # Use EventDelegate's method for consistent formatting
        delegate = EventDelegate()
        return delegate._event_to_html(event)

    def _event_passes_filter(self, event):
        """Check if event matches current filter criteria."""
        filter_text = self.filter_lineedit.text().lower()
        filter_type = self.filter_type_combo.currentText()

        # Type filter
        if filter_type != "all":
            if event.get("type") != filter_type:
                return False

        # Text filter
        if filter_text:
            content = event.get("content", "").lower()
            reasoning = event.get("reasoning", "").lower()
            tool_calls = event.get("tool_calls", [])
            tool_text = " ".join([
                tc.get("name", "") + " " + str(tc.get("arguments", ""))
                for tc in tool_calls
            ]).lower()

            if (filter_text not in content and
                filter_text not in reasoning and
                filter_text not in tool_text):
                if filter_text not in event.get("type", "").lower():
                    return False

        return True

    def _apply_filter(self):
        """Apply current filter settings and rebuild output."""
        self.filter_proxy_model.set_filter(
            self.filter_lineedit.text(),
            self.filter_type_combo.currentText()
        )
        self._rebuild_output_document()

    def _rebuild_output_document(self):
        """Rebuild the output text document from filtered events."""
        self.output_textedit.clear()
        delegate = EventDelegate()
        for row in range(self.filter_proxy_model.rowCount()):
            index = self.filter_proxy_model.index(row, 0)
            event = index.data(Qt.ItemDataRole.UserRole)
            if event:
                html = delegate._event_to_html(event)
                cursor = self.output_textedit.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                if row > 0:
                    cursor.insertHtml("<hr>")
                cursor.insertHtml(html)

    def display_event(self, event):
        """Add an event to the output display."""
        # Add to model
        self.event_model.add_event(event)

        # If event passes filter, add to output
        if self._event_passes_filter(event):
            html = self._format_event_html(event)
            cursor = self.output_textedit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            if not self.output_textedit.document().isEmpty():
                cursor.insertHtml("<hr>")
            cursor.insertHtml(html)

        self.smart_scroller.scroll_to_bottom()

    def _scroll_to_bottom(self):
        """Scroll output to bottom (for backward compatibility)."""
        self.smart_scroller.scroll_to_bottom()

    def clear_output(self):
        """Clear all output."""
        self.event_model.clear()
        self.output_textedit.clear()


    def update_tokens(self, total_input, total_output):
        """Update token counts (delegate to status panel)."""
        # This will be connected to status panel's update_tokens method
        pass

    def update_context_length(self, context_tokens):
        """Update context length (delegate to status panel)."""
        # This will be connected to status panel's update_context_length method
        pass

    def update_status(self, text):
        """Update status message (delegate to status panel)."""
        # This will be connected to status panel's update_status method
        pass

    def display_loaded_conversation(self, events):
        """Display a loaded conversation from history."""
        self.clear_output()
        for event in events:
            self.display_event(event)
