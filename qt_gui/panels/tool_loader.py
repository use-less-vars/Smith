"""Tool Loader Panel with checkboxes to enable/disable tools."""
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QCheckBox


class ToolLoaderPanel(QGroupBox):
    """Panel with checkboxes to enable/disable tools."""

    def __init__(self, tool_classes):
        super().__init__("Tool Loader")
        self.tool_classes = tool_classes

        self.tool_checkboxes = {}  # name -> QCheckBox

        layout = QVBoxLayout()
        for cls in tool_classes:
            checkbox = QCheckBox(cls.__name__)
            checkbox.setChecked(True)
            layout.addWidget(checkbox)
            self.tool_checkboxes[cls.__name__] = checkbox

        layout.addStretch()
        self.setLayout(layout)

    def get_enabled_tool_names(self):
        """Return list of enabled tool names."""
        return [name for name, cb in self.tool_checkboxes.items() if cb.isChecked()]
