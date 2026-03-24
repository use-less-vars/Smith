"""Main window for the ThoughtMachine GUI."""
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QPushButton, QMenuBar, QMenu,
    QWidget, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QAction
from session.store import FileSystemSessionStore
from qt_gui.themes import apply_theme
class AgentGUI(QMainWindow):
    """Main application window with tab management and menu bar."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ThoughtMachine")
        self._closing = False
        self.current_theme = None
        self.session_store = FileSystemSessionStore()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_current_tab_changed)
        # Add new tab button on the tab bar
        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedSize(24, 24)
        new_tab_btn.setToolTip("New Session Tab")
        new_tab_btn.clicked.connect(self.new_tab)
        self.tab_widget.setCornerWidget(new_tab_btn, Qt.Corner.TopRightCorner)
        main_layout.addWidget(self.tab_widget)
        self.new_tab(auto_load_current=True)  # create initial tab
        self.create_menu_bar()

    def new_tab(self, session_id=None, auto_load_current=False):
        from qt_gui_refactored import SessionTab
        tab = SessionTab(session_store=self.session_store, auto_load_current=auto_load_current)
        if session_id:
            try:
                tab.presenter.load_session(session_id)
                tab.display_loaded_conversation()
                tab.update_window_title()
            except Exception as e:
                print(f"[GUI] Failed to load session {session_id}: {e}")
        index = self.tab_widget.addTab(tab, tab.presenter.session_name or "Untitled")
        self.tab_widget.setCurrentWidget(tab)

    def close_tab(self, index):
        tab = self.tab_widget.widget(index)
        if tab:
            tab.close()  # triggers closeEvent; the tab will remove itself if accepted
            # If no tabs remain, create a new empty tab
            if self.tab_widget.count() == 0:
                self.new_tab()

    def on_current_tab_changed(self, index):
        tab = self.tab_widget.currentWidget()
        if tab:
            tab.update_window_title()
            self.statusBar().showMessage(f"Tokens: in={tab.total_input}, out={tab.total_output}, ctx={tab.context_length}")

    def create_menu_bar(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        # File menu
        file_menu = menu_bar.addMenu("File")
        save_config_action = QAction("Save Configuration", self)
        save_config_action.triggered.connect(lambda: self.current_tab().save_config())
        file_menu.addAction(save_config_action)
        load_config_action = QAction("Load Configuration", self)
        load_config_action.triggered.connect(lambda: self.current_tab().load_config())
        file_menu.addAction(load_config_action)
        file_menu.addSeparator()
        # Export submenu
        export_menu = file_menu.addMenu("Export Conversation")
        export_text_action = QAction("As Plain Text", self)
        export_text_action.triggered.connect(lambda: self.current_tab().export_conversation_text())
        export_menu.addAction(export_text_action)
        export_html_action = QAction("As HTML", self)
        export_html_action.triggered.connect(lambda: self.current_tab().export_conversation_html())
        export_menu.addAction(export_html_action)
        export_pdf_action = QAction("As PDF", self)
        export_pdf_action.triggered.connect(lambda: self.current_tab().export_conversation_pdf())
        export_menu.addAction(export_pdf_action)
        file_menu.addSeparator()
        # Session management actions
        save_session_action = QAction("Save Session As...", self)
        save_session_action.triggered.connect(lambda: self.current_tab().save_session_as())
        file_menu.addAction(save_session_action)
        open_session_action = QAction("Open Session...", self)
        open_session_action.triggered.connect(lambda: self.current_tab().open_session())
        file_menu.addAction(open_session_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        # View menu for theme
        view_menu = menu_bar.addMenu("View")
        theme_menu = view_menu.addMenu("Theme")
        light_theme_action = QAction("Light", self)
        light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_theme_action)
        dark_theme_action = QAction("Dark", self)
        dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        high_contrast_theme_action = QAction("High Contrast", self)
        high_contrast_theme_action.triggered.connect(lambda: self.set_theme("high_contrast"))
        theme_menu.addAction(high_contrast_theme_action)
        # Shortcuts
        save_config_action.setShortcut("Ctrl+S")
        load_config_action.setShortcut("Ctrl+O")
        exit_action.setShortcut("Ctrl+Q")

    def current_tab(self):
        return self.tab_widget.currentWidget()

    def set_theme(self, theme_name):
        """Set application theme."""
        if apply_theme(self, theme_name):
            self.current_theme = theme_name
            print(f"[GUI] Theme set to: {theme_name}")
        else:
            print(f"[GUI] Unknown theme: {theme_name}")

    def closeEvent(self, event):
        # Close all tabs by calling close() on each; if any rejects, abort the application close.
        # Tabs will remove themselves upon acceptance.
        if self._closing:
            event.accept()
            return
        self._closing = True
        print("[AgentGUI] closeEvent called")

        while self.tab_widget.count() > 0:
            tab = self.tab_widget.widget(0)
            if tab:
                if not tab.close():
                    event.ignore()
                    self._closing = False
                    return
            else:
                break
        event.accept()
        print("[AgentGUI] closeEvent accepted")
