"""
Provider Manager Dialog — table of profiles with Add / Edit / Delete.

Opens as a modal dialog with a QTableWidget showing all profiles.
Each row shows: Label, Type, URL, Default Model.
Buttons at the bottom: Add, Edit, Delete.
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QFormLayout, QLineEdit,
    QComboBox, QListWidget, QDialogButtonBox, QLabel,
)
from PyQt6.QtCore import Qt
from agent.config.provider_profile import ProviderProfile, ProviderManager


class ProviderDialog(QDialog):
    """Modal dialog with a table of provider profiles and Add/Edit/Delete."""

    def __init__(self, manager: ProviderManager, parent=None):
        super().__init__(parent)
        self._manager = manager
        self.setWindowTitle('Manage Provider Profiles')
        self.setMinimumSize(700, 400)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Label', 'Type', 'Base URL', 'Default Model'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self._on_edit)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton('Add…')
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton('Edit…')
        self.edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton('Delete')
        self.delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()
        self.close_btn = QPushButton('Close')
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(0)
        profiles = self._manager.list_profiles()
        self.table.setRowCount(len(profiles))
        for i, p in enumerate(profiles):
            self.table.setItem(i, 0, QTableWidgetItem(p.label))
            self.table.setItem(i, 1, QTableWidgetItem(p.provider_type))
            self.table.setItem(i, 2, QTableWidgetItem(p.base_url))
            self.table.setItem(i, 3, QTableWidgetItem(p.default_model))
            # Store profile id in the first column item data
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, p.id)

    def _selected_profile_id(self) -> Optional[str]:
        rows = self.table.selectedItems()
        if not rows:
            return None
        row = rows[0].row()
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_add(self):
        dlg = _ProfileEditDialog(self._manager, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._manager.save()
            self._populate_table()

    def _on_edit(self):
        profile_id = self._selected_profile_id()
        if not profile_id:
            QMessageBox.information(self, 'Edit', 'Please select a profile to edit.')
            return
        profile = self._manager.get_profile(profile_id)
        if not profile:
            return
        dlg = _ProfileEditDialog(self._manager, profile_id=profile_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._manager.save()
            self._populate_table()

    def _on_delete(self):
        profile_id = self._selected_profile_id()
        if not profile_id:
            QMessageBox.information(self, 'Delete', 'Please select a profile to delete.')
            return
        profile = self._manager.get_profile(profile_id)
        if not profile:
            return
        confirm = QMessageBox.question(
            self, 'Confirm Delete',
            f'Delete profile "{profile.label}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self._manager.delete_profile(profile_id)
            self._manager.save()
            self._populate_table()


class _ProfileEditDialog(QDialog):
    """Modal form for adding / editing a single profile."""

    def __init__(self, manager: ProviderManager, profile_id: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._manager = manager
        self._profile_id = profile_id
        self._existing = manager.get_profile(profile_id) if profile_id else None

        self.setWindowTitle('Edit Profile' if self._existing else 'Add Profile')
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.label_edit = QLineEdit()
        if self._existing:
            self.label_edit.setText(self._existing.label)
        form.addRow('Label:', self.label_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['openai_compatible', 'anthropic', 'openai'])
        if self._existing:
            idx = self.type_combo.findText(self._existing.provider_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow('Provider Type:', self.type_combo)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText('https://api.example.com')
        if self._existing:
            self.url_edit.setText(self._existing.base_url)
        form.addRow('Base URL:', self.url_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText('sk-…')
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        if self._existing and self._existing.api_key:
            self.api_key_edit.setText(self._existing.api_key)
        form.addRow('API Key:', self.api_key_edit)

        self.default_model_edit = QLineEdit()
        self.default_model_edit.setPlaceholderText('deepseek-reasoner')
        if self._existing:
            self.default_model_edit.setText(self._existing.default_model)
        form.addRow('Default Model:', self.default_model_edit)

        layout.addLayout(form)

        # Model list
        layout.addWidget(QLabel('Known Models:'))
        model_list_layout = QHBoxLayout()
        self.model_list = QListWidget()
        if self._existing:
            for m in self._existing.models:
                self.model_list.addItem(m)
        model_list_layout.addWidget(self.model_list)

        model_btn_layout = QVBoxLayout()
        self.add_model_btn = QPushButton('Add')
        self.add_model_btn.clicked.connect(self._on_add_model)
        model_btn_layout.addWidget(self.add_model_btn)

        self.remove_model_btn = QPushButton('Remove')
        self.remove_model_btn.clicked.connect(self._on_remove_model)
        model_btn_layout.addWidget(self.remove_model_btn)
        model_btn_layout.addStretch()

        model_list_layout.addLayout(model_btn_layout)
        layout.addLayout(model_list_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_add_model(self):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, 'Add Model', 'Model name:')
        if ok and text.strip():
            self.model_list.addItem(text.strip())

    def _on_remove_model(self):
        for item in self.model_list.selectedItems():
            self.model_list.takeItem(self.model_list.row(item))

    def _on_accept(self):
        label = self.label_edit.text().strip()
        if not label:
            QMessageBox.warning(self, 'Validation', 'Label is required.')
            return

        # Generate an id from the label if new, or keep existing id
        profile_id = self._profile_id or label.lower().replace(' ', '-').replace('/', '-')

        models = [self.model_list.item(i).text() for i in range(self.model_list.count())]

        profile = ProviderProfile(
            id=profile_id,
            label=label,
            provider_type=self.type_combo.currentText(),
            base_url=self.url_edit.text().strip(),
            api_key=self.api_key_edit.text().strip(),
            default_model=self.default_model_edit.text().strip(),
            models=models,
        )
        self._manager.add_profile(profile)
        self.accept()
