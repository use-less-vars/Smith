"""Conversation Model for QML ListView.

This model exposes the conversation history (session.user_history) to QML.
"""
import sys
from PyQt6.QtCore import Qt, QAbstractListModel, QModelIndex, pyqtSignal, pyqtSlot
from PyQt6.QtCore import QVariant

from agent.presenter.agent_presenter import RefactoredAgentPresenter
from qt_gui.debug_log import debug_log
from qt_gui.panels.markdown_renderer import MarkdownRenderer


class ConversationModel(QAbstractListModel):
    """QAbstractListModel for conversation messages."""
    
    # Custom roles for QML
    RoleMessageType = Qt.ItemDataRole.UserRole + 1
    RoleContent = Qt.ItemDataRole.UserRole + 2
    RoleToolName = Qt.ItemDataRole.UserRole + 3
    RoleIsFinal = Qt.ItemDataRole.UserRole + 4
    RoleRole = Qt.ItemDataRole.UserRole + 5  # 'user', 'assistant', 'system', 'tool'
    RoleIsError = Qt.ItemDataRole.UserRole + 6
    RoleHtmlContent = Qt.ItemDataRole.UserRole + 7  # For future markdown rendering
    
    def __init__(self, parent=None, presenter=None, session=None):
        """Initialize the conversation model.
        
        Args:
            parent: Parent QObject
            presenter: RefactoredAgentPresenter instance (optional)
            session: Session instance (optional, will be extracted from presenter if not provided)
        """
        super().__init__(parent)
        self._presenter = None
        self._session = None
        self._previous_row_count = 0
        
        if presenter:
            self.set_presenter(presenter)
        elif session:
            self.set_session(session)
    
    def set_presenter(self, presenter: RefactoredAgentPresenter):
        """Set the presenter and connect to its signals."""
        if self._presenter:
            # Disconnect previous presenter if any
            try:
                self._presenter.conversation_changed.disconnect(self._on_conversation_changed)
            except (TypeError, RuntimeError):
                pass  # Not connected
        
        self._presenter = presenter
        
        # Connect conversation_changed signal
        if presenter:
            presenter.conversation_changed.connect(self._on_conversation_changed)

            # Get current session if available
            if hasattr(presenter, 'session') and presenter.session:
                self._session = presenter.session
                self.beginResetModel()
                self.endResetModel()
                self._previous_row_count = self.rowCount()
            else:
                # Presenter has no session, clear the model
                self._session = None
                self.beginResetModel()
                self.endResetModel()
                self._previous_row_count = 0
        else:
            # Presenter is None, clear the model
            self._session = None
            self.beginResetModel()
            self.endResetModel()
            self._previous_row_count = 0    
    def set_session(self, session):
        """Set the session directly (used when tabs switch).
        
        Note: Without a presenter, we won't receive conversation_changed signals.
        For Phase 1, we'll rely on the presenter signal. In Phase 5, we can
        connect directly to the ObservableList callback.
        """
        self._session = session
        # For now, just reset the model
        self.beginResetModel()
        self.endResetModel()
        self._previous_row_count = self.rowCount()
    
    def _on_conversation_changed(self):
        """Handle conversation changes from presenter."""
        debug_log(f"[ConversationModel] conversation_changed signal received, row count: {self.rowCount()}", 
                  level="DEBUG")
        # Incremental update instead of full reset
        old_count = self._previous_row_count
        new_count = self.rowCount()
        
        if new_count > old_count:
            # Rows added
            self.beginInsertRows(QModelIndex(), old_count, new_count - 1)
            self.endInsertRows()
            debug_log(f"[ConversationModel] Inserted rows {old_count} to {new_count - 1}", level="DEBUG")
        elif new_count < old_count:
            # Rows removed (should not happen in normal conversation)
            self.beginRemoveRows(QModelIndex(), new_count, old_count - 1)
            self.endRemoveRows()
            debug_log(f"[ConversationModel] Removed rows {new_count} to {old_count - 1}", level="DEBUG")
        # If counts equal, maybe data changed (not implemented)
        
        self._previous_row_count = new_count
    
    def rowCount(self, parent=QModelIndex()):
        """Return number of messages in conversation history."""
        if not self._session or not hasattr(self._session, 'user_history'):
            return 0
        return len(self._session.user_history)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Return data for given index and role."""
        if not index.isValid() or index.row() >= self.rowCount():
            return QVariant()
        
        if not self._session or not hasattr(self._session, 'user_history'):
            return QVariant()
        
        message = self._session.user_history[index.row()]
        
        # Map roles to message fields
        if role == Qt.ItemDataRole.DisplayRole:
            # Return simple text representation for debugging
            content = message.get('content', '')
            if len(content) > 50:
                return content[:50] + '...'
            return content
        
        elif role == self.RoleMessageType:
            return message.get('type', '')
        
        elif role == self.RoleContent:
            return message.get('content', '')
        
        elif role == self.RoleToolName:
            return message.get('tool_name', '')
        
        elif role == self.RoleIsFinal:
            # Determine if this is a final message
            # Could check message type or tool_name == 'Final' / 'FinalReport'
            tool_name = message.get('tool_name', '')
            msg_type = message.get('type', '')
            return tool_name in ['Final', 'FinalReport'] or msg_type == 'final'
        
        elif role == self.RoleRole:
            # Map message type to role
            msg_type = message.get('type', '')
            if msg_type == 'user_query':
                return 'user'
            elif msg_type in ['tool_call', 'tool_result']:
                return 'tool'
            elif msg_type == 'system':
                return 'system'
            else:
                # Default to assistant for assistant messages
                return 'assistant'
        
        elif role == self.RoleIsError:
            return message.get('is_error', False)
        
        elif role == self.RoleHtmlContent:
            # Convert markdown to HTML using MarkdownRenderer
            content = message.get('content', '')
            if content:
                try:
                    return MarkdownRenderer.markdown_to_html(content)
                except Exception as e:
                    debug_log(f"[ConversationModel] Error converting markdown to HTML: {e}", level="ERROR")
                    # Fallback to plain text as HTML-escaped
                    import html
                    return html.escape(content)
            return ''
        
        return QVariant()
    
    def roleNames(self):
        """Return mapping of role IDs to role names for QML."""
        roles = {
            Qt.ItemDataRole.DisplayRole: b'display',
            self.RoleMessageType: b'messageType',
            self.RoleContent: b'content',
            self.RoleToolName: b'toolName',
            self.RoleIsFinal: b'isFinal',
            self.RoleRole: b'role',
            self.RoleIsError: b'isError',
            self.RoleHtmlContent: b'htmlContent',
        }
        return roles