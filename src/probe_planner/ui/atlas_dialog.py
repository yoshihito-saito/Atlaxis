"""Browse the BrainGlobe catalogue without downloading atlas volumes."""

from configparser import ConfigParser, Error as ConfigError

from brainglobe_atlasapi import config, descriptors
from brainglobe_atlasapi.list_atlases import get_downloaded_atlases, get_local_atlas_version
from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout,
)


# Chooser policy; older saved plans retain backend support for other atlases.
# Versions must have matching presets in atlas_default_coordinates.
_AUTOMATIC_ATLASES = {
    "whs_sd_rat_39um": "1.2",
    "whs_sd_swc_female_rat_39um": "1.0",
    "allen_mouse_10um": "1.2",
    "allen_mouse_25um": "1.2",
    "allen_mouse_50um": "1.2",
}


class AtlasDialog(QDialog):
    def __init__(self, current="whs_sd_rat_39um", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load atlas")
        self.resize(700, 520)
        self.downloaded = set(get_downloaded_atlases())
        self.local_versions = {
            name: get_local_atlas_version(name)
            for name in self.downloaded & _AUTOMATIC_ATLASES.keys()
        }
        self.versions = {}
        root = config.get_brainglobe_dir()
        for filename in ("last_versions.conf", "custom_atlases.conf"):
            cached = ConfigParser()
            try:
                cached.read(root / filename, encoding="utf-8")
                if cached.has_section("atlases"):
                    self.versions.update(cached.items("atlases"))
            except (OSError, ConfigError):
                # The online request below can recover an unreadable catalogue.
                pass

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Rat and mouse atlases with automatic Bregma presets."))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search atlases (e.g. rat, mouse, Allen)")
        layout.addWidget(self.search)
        self.table = QTreeWidget()
        self.table.setHeaderLabels(["Atlas", "Data"])
        self.table.setRootIsDecorated(False)
        self.table.setColumnWidth(0, 475)
        layout.addWidget(self.table, 1)
        self.status = QLabel("Checking the BrainGlobe catalogue…")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.calibration = QLabel()
        self.calibration.setWordWrap(True)
        layout.addWidget(self.calibration)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText("Load")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.table.currentItemChanged.connect(self.selection_changed)
        self.table.itemDoubleClicked.connect(lambda *_: self.accept())
        self.search.textChanged.connect(self.filter_atlases)
        self.populate(current)

        # Qt owns the request lifetime; closing the dialog does not leave a
        # running QThread, and no network work blocks the GUI thread.
        self.network = QNetworkAccessManager(self)
        request = QNetworkRequest(QUrl(descriptors.remote_url_base.format("last_versions.conf")))
        request.setTransferTimeout(10_000)
        self.reply = self.network.get(request)
        self.reply.finished.connect(self.catalogue_finished)

    @property
    def selected_name(self):
        item = self.table.currentItem()
        return item.text(0) if item is not None and not item.isHidden() else ""

    def populate(self, selected):
        self.table.blockSignals(True)
        self.table.clear()
        # BrainGlobe opens downloaded data without upgrading it. An unsupported
        # local version must not be presented as automatic based on a newer listing.
        versions = self.versions | self.local_versions
        names = sorted((name for name, version in versions.items()
                        if name in _AUTOMATIC_ATLASES
                        and version == _AUTOMATIC_ATLASES[name]), key=lambda name: (
            name not in self.downloaded,
            0 if "_rat_" in name else 1 if "_mouse_" in name else 2,
            name,
        ))
        for name in names:
            item = QTreeWidgetItem([name, "Downloaded" if name in self.downloaded else "Download on load"])
            self.table.addTopLevelItem(item)
            if name == selected:
                self.table.setCurrentItem(item)
        self.table.blockSignals(False)
        self.filter_atlases()
        if self.table.currentItem() is not None:
            self.table.scrollToItem(self.table.currentItem())

    def filter_atlases(self, *_):
        words = self.search.text().casefold().split()
        visible = []
        for index in range(self.table.topLevelItemCount()):
            item = self.table.topLevelItem(index)
            matches = all(word in item.text(0).casefold() for word in words)
            item.setHidden(not matches)
            if matches:
                visible.append(item)
        if not self.selected_name:
            self.table.setCurrentItem(visible[0] if visible else None)
        self.selection_changed()

    def selection_changed(self, *_):
        name = self.selected_name
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(bool(name))
        self.calibration.setText(
            "Waxholm-registered female rat: automatic Waxholm Bregma in the packaged atlas grid."
            if name == "whs_sd_swc_female_rat_39um" else
            "Bregma is set automatically from the Waxholm atlas landmark."
            if name == "whs_sd_rat_39um" else
            "Estimated Allen CCF Bregma with 5° skull-level pitch correction; not individual-animal registration."
            if name else "No matching atlas. Try a different search."
        )

    def catalogue_finished(self):
        try:
            if self.reply.error() != QNetworkReply.NoError:
                raise ValueError(self.reply.errorString())
            catalogue = ConfigParser()
            catalogue.read_string(bytes(self.reply.readAll()).decode("utf-8"))
            versions = dict(catalogue.items("atlases"))
            if not versions:
                raise ValueError("The atlas catalogue is empty.")
            selected = self.selected_name
            self.versions.update(versions)
            self.populate(selected)
            self.status.setText(
                f"{self.table.topLevelItemCount()} supported atlases · "
                "Missing data downloads when you click Load."
            )
        except (ValueError, ConfigError, UnicodeError) as error:
            self.status.setText("Catalogue refresh unavailable; showing locally known atlases.")
            self.status.setToolTip(str(error))
        finally:
            self.reply.deleteLater()

    def accept(self):
        if self.selected_name:
            super().accept()
