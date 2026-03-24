"""MCP Configuration Dialog for managing MCP servers."""
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton,
    QInputDialog
)


class MCPConfigDialog(QDialog):
    """Dialog for configuring MCP servers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MCP Configuration")
        self.mcp_config_path = "mcp_config.json"
        self.config = self._load_config()
        self._setup_ui()

    def _load_config(self):
        """Load MCP configuration from file."""
        try:
            with open(self.mcp_config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"servers": []}

    def _save_config(self):
        """Save MCP configuration to file."""
        with open(self.mcp_config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Server list
        self.server_list = QListWidget()
        layout.addWidget(self.server_list)
        self._refresh_list()

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.remove_btn = QPushButton("Remove")
        self.save_btn = QPushButton("Save")
        self.reload_btn = QPushButton("Reload")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.reload_btn)
        layout.addLayout(btn_layout)

        # Connect signals
        self.add_btn.clicked.connect(self._add_server)
        self.remove_btn.clicked.connect(self._remove_server)
        self.save_btn.clicked.connect(self._save_config)
        self.reload_btn.clicked.connect(self._reload_config)

    def _refresh_list(self):
        """Refresh the server list display."""
        self.server_list.clear()
        for server in self.config.get("servers", []):
            name = server.get('name', 'Unnamed')
            # Determine display field based on transport
            transport = server.get('transport', 'http')
            if transport == 'stdio':
                display = server.get('command', 'N/A')
            else:
                display = server.get('url', server.get('host', 'N/A'))
            self.server_list.addItem(f"{name} - {display}")

    def _add_server(self):
        """Add a new MCP server."""
        name, ok = QInputDialog.getText(self, "Add Server", "Name:")
        if not ok or not name:
            return
        # Transport selection
        transports = ["stdio", "http", "sse"]
        transport, ok = QInputDialog.getItem(
            self, "Add Server", "Transport:", transports, 0, False
        )
        if not ok:
            return
        server = {"name": name, "transport": transport}
        if transport == "stdio":
            command, ok = QInputDialog.getText(self, "Add Server", "Command (e.g., python):")
            if ok and command:
                server["command"] = command
                args, ok = QInputDialog.getText(self, "Add Server", "Arguments (space-separated):")
                if ok and args:
                    server["args"] = args.split()
        else:
            url, ok = QInputDialog.getText(self, "Add Server", "URL:")
            if ok and url:
                server["url"] = url
        self.config.setdefault("servers", []).append(server)
        self._refresh_list()

    def _remove_server(self):
        """Remove the selected MCP server."""
        row = self.server_list.currentRow()
        if row >= 0 and self.config.get("servers"):
            self.config["servers"].pop(row)
            self._refresh_list()

    def _reload_config(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        self._refresh_list()
