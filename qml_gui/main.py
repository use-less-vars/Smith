#!/usr/bin/env python3
"""
Minimal QML GUI for ThoughtMachine.
"""

import os
import sys
import json
from pathlib import Path
from PyQt6.QtCore import QLibraryInfo
from dotenv import load_dotenv

# Add parent directory to Python path to allow importing agent, session, etc.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from agent.presenter.agent_presenter import RefactoredAgentPresenter
class StatusBridge(QObject):
    """Bridge for status updates from presenter to QML."""
    
    tokensUpdated = pyqtSignal(int, int)
    contextUpdated = pyqtSignal(int)
    stateChanged = pyqtSignal(str)
    
    def __init__(self, presenter, parent=None):
        super().__init__(parent)
        self.presenter = presenter
        self._connect_presenter()
    
    def _connect_presenter(self):
        self.presenter.tokens_updated.connect(self.tokensUpdated)
        self.presenter.context_updated.connect(self.contextUpdated)
        self.presenter.state_changed.connect(self._on_state_changed)
    
    @pyqtSlot(object)
    def _on_state_changed(self, state):
        # Convert ExecutionState to string
        self.stateChanged.emit(str(state))


class FileDialogBridge(QObject):
    pathSelected = pyqtSignal(str, str)  # path, tag

    @pyqtSlot(str, str)
    def openFileDialog(self, start_path: str = "", tag: str = ""):
        path = QFileDialog.getExistingDirectory(None, "Select Directory", start_path)
        if path:
            self.pathSelected.emit(path, tag)

from qml_gui.models.conversation_model import ConversationModel


def load_config() -> dict:
    """Load configuration from environment variables and config file."""
    # Load environment variables from .env file
    load_dotenv()
    
    config = {}

    # 1. Environment variables
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('DEEPSEEK_API_KEY')    
    model = os.getenv('MODEL')
    base_url = os.getenv('BASE_URL')
    
    if api_key:
        config['api_key'] = api_key
    if model:
        config['model'] = model
    if base_url:
        config['base_url'] = base_url
    
    # Determine provider type based on environment or api key source
    if os.getenv('DEEPSEEK_API_KEY'):
        config['provider_type'] = 'openai_compatible'
        # Default DeepSeek URL if not set
        if 'base_url' not in config:
            config['base_url'] = 'https://api.deepseek.com'
    elif os.getenv('OPENAI_API_KEY'):
        config['provider_type'] = 'openai'
        # Default OpenAI URL if not set
        if 'base_url' not in config:
            config['base_url'] = 'https://api.openai.com/v1'
    
    # 2. Config file: ~/.thoughtmachine/config.json
    config_dir = Path.home() / '.thoughtmachine'
    config_file = config_dir / 'config.json'
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
            # Merge file config (overwrites env vars) but skip empty strings for API fields
            for key, value in file_config.items():
                # Skip empty strings for api_key, model, base_url to allow env vars to work
                if isinstance(value, str) and value == '' and key in ['api_key', 'model', 'base_url']:
                    continue
                config[key] = value
        except Exception as e:
            print(f"Warning: Failed to load config file {config_file}: {e}")
    
    # 3. Also check for agent_config.json in project root (legacy)
    project_config = Path(project_root) / 'agent_config.json'
    if project_config.exists():
        try:
            with open(project_config, 'r') as f:
                project_config_data = json.load(f)
            # Merge project config (lower priority than user config)
            for key, value in project_config_data.items():
                if key not in config:
                    config[key] = value
        except Exception as e:
            print(f"Warning: Failed to load project config {project_config}: {e}")
    
    return config


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("ThoughtMachine QML")
    app.setOrganizationName("ThoughtMachine")
    
    # Create presenter (backend)
    presenter = RefactoredAgentPresenter()
    
    # Load configuration from environment/file and apply to presenter
    config = load_config()
    if config:
        print(f"Loaded config with keys: {list(config.keys())}")
        presenter.update_config(config)
    else:
        print("No configuration found. Agent will not run until API key is set via config dialog.")
    
    # Create conversation model
    conversation_model = ConversationModel(presenter)

    # Create status bridge
    status_bridge = StatusBridge(presenter)
    file_dialog_bridge = FileDialogBridge()
    
    engine = QQmlApplicationEngine()

    
    # Expose model to QML as a context property
    engine.rootContext().setContextProperty("conversationModel", conversation_model)
    # Expose presenter to QML as a context property
    engine.rootContext().setContextProperty("presenter", presenter)
    engine.rootContext().setContextProperty("statusBridge", status_bridge)
    engine.rootContext().setContextProperty("fileDialogBridge", file_dialog_bridge)
    
    # Load the main QML file
    qml_path = os.path.join(os.path.dirname(__file__), "qml", "MainWindow.qml")
    engine.load(qml_path)
    
    if not engine.rootObjects():
        print("Failed to load QML file", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()