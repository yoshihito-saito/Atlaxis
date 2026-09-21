"""First-run data selection; changed destinations apply on the next launch."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from probe_planner.storage import (
    DataPaths, activate_storage, default_paths, prepare_storage, saved_paths, save_paths,
)


class DataFoldersDialog(QDialog):
    def __init__(self, initial, parent=None, *, first_run=False):
        super().__init__(parent)
        self.paths = initial
        self.setWindowTitle("Atlaxis data folder")
        self.resize(640, 220)
        layout = QVBoxLayout(self)
        introduction = QLabel(
            "Choose where Atlaxis stores probes, atlases and plans."
            if first_run else "Folder changes take effect after restarting Atlaxis."
        )
        introduction.setWordWrap(True)
        layout.addWidget(introduction)
        form = QFormLayout()
        self.data_root = QLineEdit(str(initial.root))
        row = QHBoxLayout()
        row.addWidget(self.data_root)
        button = QPushButton("Browse…")
        button.clicked.connect(self.browse)
        row.addWidget(button)
        form.addRow("Atlaxis folder", row)
        layout.addLayout(form)
        description = QLabel(
            "Creates probes/standard, probes/custom, atlases and planning inside this folder.\n"
            "Standard probes are copied; edited files and custom probes are kept.\n"
            "Existing plans and atlas downloads elsewhere are not moved."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText("Set up" if first_run else "Save for next launch")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def browse(self):
        chosen = QFileDialog.getExistingDirectory(
            self, "Choose where to create Atlaxis",
            str(Path(self.data_root.text()).expanduser().parent),
        )
        if chosen:
            location = Path(chosen)
            root = location if location.name.lower() == "atlaxis" else location / "Atlaxis"
            self.data_root.setText(str(root))

    def accept(self):
        if not self.data_root.text().strip():
            QMessageBox.warning(self, "Data folder", "Choose an Atlaxis folder.")
            return
        paths = DataPaths(Path(self.data_root.text().strip()).expanduser().resolve())
        self.buttons.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            preserved = prepare_storage(paths)
            save_paths(paths)
        except Exception as error:
            QApplication.restoreOverrideCursor()
            self.buttons.setEnabled(True)
            QMessageBox.critical(self, "Unable to prepare data folders", str(error))
            return
        QApplication.restoreOverrideCursor()
        self.paths = paths
        if preserved:
            QMessageBox.information(self, "Probe files preserved",
                f"Kept {len(preserved)} edited or existing probe files. They were not overwritten.")
        super().accept()


def initialize_storage():
    """Finish setup before any import of BrainGlobe reads its configuration."""
    paths = saved_paths()
    if paths is not None:
        try:
            prepare_storage(paths)
            activate_storage(paths)
        except Exception as error:
            QMessageBox.warning(None, "Data folder unavailable", str(error))
        else:
            return True
    while True:
        dialog = DataFoldersDialog(paths or default_paths(), first_run=True)
        accepted = dialog.exec() == QDialog.Accepted
        paths = dialog.paths
        dialog.deleteLater()
        if not accepted:
            return False
        try:
            activate_storage(paths)
        except Exception as error:
            QMessageBox.warning(None, "Data folder unavailable", str(error))
        else:
            return True
