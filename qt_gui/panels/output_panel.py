"""Output Panel - Event display and output area for the agent."""
import html
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTextEdit, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor

from ..debug_log import debug_log
from .markdown_renderer import MarkdownRenderer


class OutputPanel(QWidget):
    """Panel containing event display, filtering, and query controls."""
    # Special tools that should have blue styling, no truncation, full markdown
    SPECIAL_TOOLS = ["Final", "FinalReport", "RequestUserInteraction"]

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Filter state tracking (keep UI but filter logic will be replaced later)
        self._last_filter_text = ""
        self._last_filter_type = "all"
        
        # Token tracking (mirrored from SessionTab)
        self.total_input = 0
        self.total_output = 0
        self.context_length = 0
        
        # Tool call mapping for special styling
        self._tool_call_map = {}  # tool_call_id -> tool_name
        
        self.init_ui()
        self.markdown_renderer = MarkdownRenderer()
        self.setup_signal_connections()
        
    def init_ui(self):
        """Initialize the output panel UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Filter controls (keep UI, functionality will be updated later)
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
            "all", "turn", "final", "user_query", "processing", "stopped",
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

    def setup_signal_connections(self):
        """Connect filter signals."""
        self.filter_lineedit.textChanged.connect(self._apply_filter)
        self.filter_type_combo.currentTextChanged.connect(self._apply_filter)

    def _apply_filter(self):
        """Apply current filter settings and rebuild output.
        TODO: Replace with new filtering logic in Phase 5."""
        filter_text = self.filter_lineedit.text()
        filter_type = self.filter_type_combo.currentText()
        # Skip if filter hasn't changed
        if filter_text == self._last_filter_text and filter_type == self._last_filter_type:
            return
        self._last_filter_text = filter_text
        self._last_filter_type = filter_type
        debug_log(f"[OutputPanel] _apply_filter: text='{filter_text}', type='{filter_type}'")
        # For now, just log. In Phase 5 we will integrate with _should_display.
        # TODO: trigger re-rendering of visible events.

    # ========== New rendering pipeline (Phase 2) ==========

    def display_event(self, event: dict) -> None:
        """Single entry point for all events from the presenter."""
        debug_log(f"DEBUG display_event keys: {list(event.keys())}", level="DEBUG", component="OutputPanel")
        debug_log(f"DEBUG display_event content sample: {str(event)[:200]}", level="DEBUG", component="OutputPanel")
        if not self._should_display(event):
            return
        html = self._render_event(event)
        self._append_html(html)

    def _should_display(self, event) -> bool:
        """Decide whether this event should be shown in the output.
        Later this can be made configurable via user settings.
        For now, always return True."""
        # TODO: Integrate with filter UI in Phase 5
        return True

    def _render_event(self, event) -> str:
        """Convert any event to a self-contained HTML block."""
        event_type = event.get("type", "unknown")
        content = event.get("content", "")
        tool_calls = event.get("tool_calls", [])
        reasoning_content = event.get("reasoning_content", "")
        tool_call_id = event.get("tool_call_id", "")
        
        # Store tool call mapping for special styling
        if event_type == "tool_call":
            tool_name = event.get("function", {}).get("name", "unknown")
            tool_call_id = event.get("id", "")
            if tool_call_id:
                self._tool_call_map[tool_call_id] = tool_name
        
        # Determine styling based on type
        if event_type == "user_query":
            border_color = "#FF69B4"
            bg_color = "#FFF0F5"
            header = "User"
        elif event_type == "turn":  # assistant message
            border_color = "#99ccff"
            bg_color = "#e6f3ff"
            header = "Assistant"
        elif event_type == "tool_call":
            tool_name = event.get("function", {}).get("name", "unknown")
            if tool_name in self.SPECIAL_TOOLS:
                border_color = "#3498db"
                bg_color = "#eef4ff"
                header = f"Tool: {tool_name}"
            else:
                border_color = "#006400"
                bg_color = "#f0f8f0"
                header = f"Tool: {tool_name}"
        elif event_type == "tool_result":
            # Look up tool name for special styling
            tool_name = self._tool_call_map.get(tool_call_id, "")
            if tool_name in self.SPECIAL_TOOLS:
                border_color = "#3498db"
                bg_color = "#eef4ff"
                header = f"Tool Result ({tool_name})"
            else:
                border_color = "#006400"
                bg_color = "#f0f8f0"
                header = "Tool Result"
        elif event_type in ("system", "token_warning", "turn_warning"):
            border_color = "#ff9999"
            bg_color = "#ffe6e6"
            header = "System"
        elif event_type == "final":
            border_color = "#FFA500"
            bg_color = "#FFF5E6"
            header = "Final"
        else:
            border_color = "#cccccc"
            bg_color = "#f8f8f8"
            header = event_type.replace('_', ' ').title()
        
        # Render content with markdown
        rendered_content = self._render_content(content)
        
        # Handle reasoning content for assistant messages
        reasoning_html = ""
        if reasoning_content:
            reasoning_html = f'''<div style="background-color: #f8f8f8; border-left: 4px solid #888; padding: 8px; margin-bottom: 12px;"><div style="color: #333; font-weight: bold;">Reasoning:</div>{self._render_content(reasoning_content)}</div>'''
        
        # Build HTML
        html_block = f'''<div style="border: 1px solid {border_color}; border-radius: 5px; margin-bottom: 12px; overflow: hidden;"><div style="background-color: {bg_color}; padding: 8px 10px; font-weight: bold; border-bottom: 1px solid {border_color};">{header}</div><div style="padding: 10px;">{reasoning_html}{rendered_content}</div></div>'''
        
        # For tool calls, optionally show arguments
        if event_type == "tool_call":
            arguments = event.get("function", {}).get("arguments", "{}")
            args_str = str(arguments)
            if len(args_str) > 200:
                args_str = args_str[:200] + '...'
            escaped_args = html.escape(args_str)
            tool_name = event.get("function", {}).get("name", "unknown")
            if tool_name not in self.SPECIAL_TOOLS:
                # Add arguments for regular tools
                html_block += f'''<div style="margin-left: 20px; margin-top: 5px; margin-bottom: 5px;"><div style="color: #666666; font-size: 0.9em; font-family: monospace, monospace;">Arguments: {escaped_args}</div></div>'''
        
        return html_block
    
    def _render_content(self, content: str) -> str:
        """Render message content to HTML (handles markdown)."""
        if not content:
            return ''
        # Use the markdown renderer
        return self.markdown_renderer.markdown_to_html(content)



    def _append_html(self, html: str) -> None:
        cursor = self.output_textedit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock()          # start a new block
        cursor.insertHtml(html)
        cursor.insertBlock()          # separate from next event
        self.output_textedit.setTextCursor(cursor)
        self._auto_scroll_if_bottom()

    def _auto_scroll_if_bottom(self) -> None:
        scrollbar = self.output_textedit.verticalScrollBar()
        if scrollbar.value() >= scrollbar.maximum() - 5:
            self.output_textedit.ensureCursorVisible()
    
    def set_updates_enabled(self, enabled: bool) -> None:
        """Enable or disable widget updates for bulk operations."""
        self.output_textedit.setUpdatesEnabled(enabled)
    
    def load_session_history(self, history, suppress_scroll: bool = True) -> None:
        """Bulk load session history without jumping.
        
        Args:
            history: List of event dicts from session.user_history
            suppress_scroll: If True, disable auto-scroll during bulk load
        """
        if suppress_scroll:
            self.set_updates_enabled(False)
        
        self.clear_output()
        for event in history:
            self.display_event(event)
        
        if suppress_scroll:
            self.set_updates_enabled(True)
            self._auto_scroll_if_bottom()
    
    def show_processing_indicator(self, query, turn_number):
        """Show a temporary 'Processing...' indicator for a user query."""
        from datetime import datetime
        
        # Create a temporary processing event
        event = {
            "type": "processing",
            "content": f"⏳ Processing your query: {query[:50]}{'...' if len(query) > 50 else ''}",
            "turn": turn_number,
            "timestamp": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "_detail_level": "normal",
            "_is_processing_indicator": True  # Marker to identify processing events
        }
        
        # Display directly (no model tracking)
        self.display_event(event)

    def remove_processing_indicator(self, turn_number):
        """Remove the processing indicator for a given turn.
        
        Note: This is a stub for compatibility; processing indicators
        are temporary and will be replaced by actual events.
        """
        pass  # No tracking needed in new implementation

    # ========== Legacy methods (to be removed or adapted) ==========

    # Keep _normalize_turn for now (used by old code)
    def _normalize_turn(self, turn_val):
        """Convert turn value to integer for consistent comparison."""
        if turn_val is None:
            return 0
        # Handle int/float turn values
        if isinstance(turn_val, (int, float)):
            return int(turn_val)
        # Handle string turn values
        if isinstance(turn_val, str):
            try:
                return int(turn_val)
            except (ValueError, TypeError):
                # Try to convert float string
                try:
                    return int(float(turn_val))
                except (ValueError, TypeError):
                    return 0
        # Fallback
        return 0

    # Old display methods (to be deleted in Phase 2)
    # We'll keep them commented out for now.
    
    # Compatibility methods for Phase 4 transition
    def clear_output(self):
        """Clear the output text edit."""
        self.output_textedit.clear()
    
    def _role_to_event_type(self, message):
        """Convert a message with 'role' to appropriate event type."""
        role = message.get('role')
        
        if role == 'user':
            return 'user_query'
        elif role == 'assistant':
            return 'turn'
        elif role == 'tool':
            # Determine if tool call or result
            if 'tool_call_id' in message:
                return 'tool_result'
            else:
                return 'tool_call'
        elif role == 'system':
            return 'system'
        else:
            # Fallback to unknown, will be displayed with role as header
            return 'unknown'
    
    def display_message(self, message):
        """Display a message from user_history.
        
        Args:
            message: A message dict from session.user_history.
                    Should have 'role' and 'content' keys.
        """
        debug_log(f"DEBUG display_message keys: {list(message.keys())}", level="DEBUG", component="OutputPanel")
        debug_log(f"DEBUG display_message role: {message.get('role')}", level="DEBUG", component="OutputPanel")
        # Convert message to event format if needed
        event = message.copy()  # Create copy to avoid modifying original
        
        # Map role to event type if type not present
        if 'type' not in event:
            event['type'] = self._role_to_event_type(message)
            debug_log(f"DEBUG display_message mapped type: {event['type']}", level="DEBUG", component="OutputPanel")
        
        # Ensure required fields
        if 'content' not in event:
            event['content'] = ''
        
        self.display_event(event)
    
    # Smart scroller compatibility (was removed in Phase 1)
    @property
    def smart_scroller(self):
        """Dummy smart scroller for compatibility during transition."""
        class DummySmartScroller:
            def pause_tracking(self): pass
            def resume_tracking(self): pass
            def scroll_to_bottom(self): pass
        return DummySmartScroller()
    
    # Event model compatibility (was removed in Phase 4)
    @property
    def event_model(self):
        """Dummy event model for compatibility during transition."""
        class DummyEventModel:
            def __init__(self):
                self.events = []
            def rowCount(self):
                return len(self.events)
            def index(self, i, col):
                return None
            def data(self, index, role):
                return None
        return DummyEventModel()
    
    @property
    def filter_proxy_model(self):
        """Dummy filter proxy model for compatibility during transition."""
        return self.event_model  # Return same dummy object
