"""Browse the BrainGlobe catalogue without downloading atlas volumes."""

from configparser import ConfigParser, Error as ConfigError

from brainglobe_atlasapi import config, descriptors
from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout,
)

from probe_planner.atlas.catalogue import S3_VERSIONS, local_atlases, supported_version


class AtlasDialog(QDialog):
    def __init__(self, current="whs_sd_rat_39um", parent=None, *, current_version=None):
        super().__init__(parent)
        self.setWindowTitle("Load atlas")
        self.resize(700, 520)
        root = config.get_brainglobe_dir()
        self.downloaded = local_atlases(root)
        # Pin recognized grids so first-launch candidates need no network request.
        self.versions = S3_VERSIONS.copy()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Rat and mouse atlases with automatic Bregma presets."))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search atlases (e.g. rat, mouse, Allen)")
        layout.addWidget(self.search)
        self.table = QTreeWidget()
        self.table.setHeaderLabels(["Atlas", "Version", "Data"])
        self.table.setRootIsDecorated(False)
        self.table.setColumnWidth(0, 340)
        self.table.setColumnWidth(1, 65)
        layout.addWidget(self.table, 1)
        self.status = QLabel(
            "Checking the BrainGlobe S3 catalogue… "
            "Missing data downloads when you click Load."
        )
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
        self.populate((current, current_version or self.versions.get(current)))

        # Qt owns the request lifetime; closing the dialog does not leave a
        # running QThread, and no network work blocks the GUI thread.
        self.network = QNetworkAccessManager(self)
        request = QNetworkRequest(QUrl(descriptors.remote_url_s3_http.format("atlases/last_versions.conf")))
        request.setTransferTimeout(90_000)
        self.reply = self.network.get(request)
        self.reply.finished.connect(self.catalogue_finished)

    @property
    def selected_name(self):
        item = self.table.currentItem()
        return item.text(0) if item is not None and not item.isHidden() else ""

    @property
    def selected_version(self):
        item = self.table.currentItem()
        return item.text(1) if self.selected_name else None

    def populate(self, selected):
        self.table.blockSignals(True)
        self.table.clear()
        pairs = sorted((pair for pair in (set(self.versions.items()) | self.downloaded)
                        if supported_version(*pair)), key=lambda pair: (
            pair not in self.downloaded,
            0 if "_rat_" in pair[0] else 1 if "_mouse_" in pair[0] else 2,
            pair,
        ))
        for name, version in pairs:
            legacy = int(version.split(".")[0]) < 3
            data = ("Local (legacy)" if legacy else "Cached (completes on load)"
                    if (name, version) in self.downloaded else "Download on load")
            item = QTreeWidgetItem([name, version, data])
            self.table.addTopLevelItem(item)
            if (name, version) == selected:
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
            selected = self.selected_name, self.selected_version
            self.versions.update({name: version.replace("_", ".") for name, version in versions.items()
                                  if name in S3_VERSIONS
                                  and supported_version(name, version.replace("_", "."))
                                  and version.replace("_", ".").startswith("3.")})
            self.populate(selected)
            self.status.setText(
                f"{self.table.topLevelItemCount()} supported atlases · "
                "Missing data downloads when you click Load."
            )
        except (ValueError, ConfigError, UnicodeError) as error:
            self.status.setText(
                "Catalogue refresh unavailable; showing supported atlas candidates. "
                "Downloading missing data requires an internet connection."
            )
            self.status.setToolTip(str(error))
        finally:
            self.reply.deleteLater()

    def accept(self):
        if self.selected_name:
            super().accept()
