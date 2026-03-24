"""Main entry point for the ThoughtMachine GUI."""
import sys
from PyQt6.QtWidgets import QApplication
from qt_gui.main_window import AgentGUI


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    gui = AgentGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
