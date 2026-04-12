#!/usr/bin/env python3
"""
Minimal QML GUI for ThoughtMachine.
"""

import os
import sys

# Add parent directory to Python path to allow importing agent, session, etc.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from agent.presenter.agent_presenter import RefactoredAgentPresenter
from qml_gui.models.conversation_model import ConversationModel


def main():
    """Application entry point."""
    app = QGuiApplication(sys.argv)
    app.setApplicationName("ThoughtMachine QML")
    app.setOrganizationName("ThoughtMachine")
    
    # Create presenter (backend)
    presenter = RefactoredAgentPresenter()
    
    # Create conversation model
    conversation_model = ConversationModel(presenter)
    
    engine = QQmlApplicationEngine()
    
    # Expose model to QML as a context property
    engine.rootContext().setContextProperty("conversationModel", conversation_model)
    
    # Load the main QML file
    qml_path = os.path.join(os.path.dirname(__file__), "qml", "MainWindow.qml")
    engine.load(qml_path)
    
    if not engine.rootObjects():
        print("Failed to load QML file", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()