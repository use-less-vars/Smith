"""
Provider Selector Widget — replaces the individual api_key/base_url/model fields.

Shows a profile dropdown, model dropdown (editable), and a Manage… button.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QPushButton, QLabel,
)
from PyQt6.QtCore import pyqtSignal, Qt
from agent.config.provider_profile import ProviderManager


class ProviderSelector(QWidget):
    """Horizontal widget: [Profile: … ▼] [Model: … ▼] [Manage…]"""

    profile_changed = pyqtSignal(str)       # profile_id
    model_changed = pyqtSignal(str)          # model name
    manage_requested = pyqtSignal()          # user clicked Manage…

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = ProviderManager()
        self._ignore_signals = False

        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel('Profile:'))
        self.profile_combo = QComboBox()
        self.profile_combo.setEditable(False)
        self.profile_combo.setMinimumWidth(160)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)
        layout.addWidget(self.profile_combo)

        layout.addWidget(QLabel('Model:'))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setMinimumWidth(180)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(self.model_combo)

        self.manage_btn = QPushButton('Manage…')
        self.manage_btn.setMaximumWidth(80)
        self.manage_btn.clicked.connect(self._on_manage)
        layout.addWidget(self.manage_btn)

        layout.addStretch()
        self.refresh()

    # ── Public API ──────────────────────────────────────────────

    def refresh(self):
        """Reload profiles from disk and rebuild the dropdown."""
        self._manager = ProviderManager()
        self._rebuild_profile_combo()

    def set_active_profile(self, profile_id: str | None):
        """Set the active profile in the dropdown."""
        self._ignore_signals = True
        idx = self.profile_combo.findData(profile_id)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        self._ignore_signals = False
        self._update_model_combo()

    def set_model(self, model: str | None):
        """Set the model combo to a specific value."""
        if model:
            self.model_combo.setCurrentText(model)

    @property
    def active_profile_id(self) -> str | None:
        data = self.profile_combo.currentData()
        return data if data else None

    @property
    def active_model(self) -> str:
        return self.model_combo.currentText().strip()

    @property
    def manager(self) -> ProviderManager:
        return self._manager

    # ── Internal ────────────────────────────────────────────────

    def _rebuild_profile_combo(self):
        self._ignore_signals = True
        self.profile_combo.clear()
        profiles = self._manager.list_profiles()
        active_id = self._manager.active_profile_id
        selected_idx = -1
        for i, p in enumerate(profiles):
            self.profile_combo.addItem(p.label, p.id)
            if p.id == active_id:
                selected_idx = i
        if selected_idx >= 0:
            self.profile_combo.setCurrentIndex(selected_idx)
        self._ignore_signals = False
        self._update_model_combo()

    def _update_model_combo(self):
        """Populate model dropdown based on the current profile."""
        self._ignore_signals = True
        profile_id = self.active_profile_id
        profile = self._manager.get_profile(profile_id) if profile_id else None

        current_text = self.model_combo.currentText()
        self.model_combo.clear()

        # Gather model candidates: start with profile.models, ensure default_model is included
        model_candidates = []
        if profile:
            if profile.models:
                model_candidates.extend(profile.models)
            if profile.default_model and profile.default_model not in model_candidates:
                model_candidates.insert(0, profile.default_model)

        if model_candidates:
            self.model_combo.addItems(model_candidates)
            # Restore previous selection if still valid
            idx = self.model_combo.findText(current_text)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            elif profile and profile.default_model:
                self.model_combo.setCurrentText(profile.default_model)
        else:
            # Fallback defaults when no profile or neither models nor default_model
            self.model_combo.addItems([
                'deepseek-reasoner', 'gpt-4', 'claude-3', 'llama-3',
            ])

        self._ignore_signals = False

    def _on_profile_selected(self, idx: int):
        if self._ignore_signals:
            return
        profile_id = self.profile_combo.itemData(idx)
        if profile_id:
            self._manager.active_profile_id = profile_id
            self._manager.save()
        self._update_model_combo()
        self.profile_changed.emit(profile_id)

    def _on_model_changed(self, text: str):
        if self._ignore_signals:
            return
        self.model_changed.emit(text)

    def _on_manage(self):
        self.manage_requested.emit()
