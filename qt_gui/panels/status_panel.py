"""Status Panel showing current status and token usage."""
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel


class StatusPanel(QGroupBox):
    """Shows current status and token usage."""

    def __init__(self, parent=None, session_store=None):
        super().__init__("Status")
        layout = QVBoxLayout()
        self.status_label = QLabel("Ready")
        self.token_label = QLabel("Tokens: 0 in / 0 out")
        layout.addWidget(self.status_label)
        self.context_label = QLabel("Context: 0 tokens")
        layout.addWidget(self.context_label)
        layout.addWidget(self.token_label)
        layout.addStretch()
        self.setLayout(layout)

    def update_status(self, text):
        """Update the status text."""
        self.status_label.setText(text)

    def format_tokens(self, tokens):
        """Format token count in thousands with 'k' suffix."""
        if tokens >= 1000:
            return f"{tokens // 1000}k"
        return str(tokens)

    def update_tokens(self, total_input, total_output):
        """Update token usage display."""
        in_text = self.format_tokens(total_input)
        out_text = self.format_tokens(total_output)
        self.token_label.setText(f"Tokens: {in_text} in / {out_text} out")

    def update_context_length(self, context_tokens):
        """Update context length display."""
        text = self.format_tokens(context_tokens)
        self.context_label.setText(f"Context: {text} tokens")
