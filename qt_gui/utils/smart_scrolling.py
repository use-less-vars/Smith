"""Smart scrolling management for QTextEdit widgets."""
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QTextEdit


class SmartScroller(QObject):
    """Manages auto-scrolling behavior for a QTextEdit.
    
    Features:
    - Auto-scroll to bottom when new content is added
    - Disable auto-scroll when user manually scrolls away
    - Re-enable auto-scroll when user scrolls back to bottom
    - Programmatic scroll support with re-entrancy guard
    """
    
    def __init__(self, text_edit: QTextEdit):
        """Initialize smart scroller for a text edit widget."""
        super().__init__()
        self._text_edit = text_edit
        self._auto_scroll_enabled = True
        self._user_scrolled_away = False
        self._programmatic_scroll = False
        
        # Connect to scrollbar changes
        scrollbar = self._text_edit.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scrollbar_value_changed)
        
    def _on_scrollbar_value_changed(self, value: int):
        """Handle scrollbar value change to detect user scrolling."""
        scrollbar = self._text_edit.verticalScrollBar()
        max_val = scrollbar.maximum()
        # If user is within 10 pixels of bottom, consider them at bottom
        self._user_scrolled_away = value < max_val - 10
        self._auto_scroll_enabled = not self._user_scrolled_away
        
    def scroll_to_bottom(self):
        """Scroll to bottom if auto-scroll is enabled."""
        if self._auto_scroll_enabled:
            self._do_scroll_to_bottom()
            
    def _do_scroll_to_bottom(self):
        """Programmatically scroll to bottom."""
        self._programmatic_scroll = True
        scrollbar = self._text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._programmatic_scroll = False
        
    def set_auto_scroll_enabled(self, enabled: bool):
        """Enable/disable auto-scrolling."""
        self._auto_scroll_enabled = enabled
        if enabled:
            self.scroll_to_bottom()
            
    def is_auto_scroll_enabled(self) -> bool:
        """Check if auto-scroll is currently enabled."""
        return self._auto_scroll_enabled
    
    def force_scroll_to_bottom(self):
        """Force scroll to bottom regardless of auto-scroll setting."""
        self._do_scroll_to_bottom()
