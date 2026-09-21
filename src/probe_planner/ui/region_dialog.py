"""Select existing atlas annotations; no custom segmentation or relabeling."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QLabel, QDialogButtonBox, QPushButton,
)


class RegionDialog(QDialog):
    def __init__(self, structures, selected_ids, atlas_name, parent=None, available_ids=None):
        super().__init__(parent)
        self.setWindowTitle("Region mask")
        self.resize(620, 620)
        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name or acronym")
        layout.addWidget(self.search)
        row = QHBoxLayout()
        select_all = QPushButton("Select all")
        select_all.clicked.connect(self.select_all)
        row.addWidget(select_all)
        clear = QPushButton("Select none")
        clear.clicked.connect(self.clear_selection)
        row.addWidget(clear)
        row.addStretch()
        expand = QPushButton("Expand all")
        expand.clicked.connect(lambda: self.tree.expandAll())
        row.addWidget(expand)
        collapse = QPushButton("Collapse")
        collapse.clicked.connect(lambda: self.tree.collapseAll())
        row.addWidget(collapse)
        layout.addLayout(row)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Region / layer", "Acronym"])
        self.items = {}
        available = set(structures if available_ids is None else available_ids)
        visible_ids = available | {ancestor for region_id in available
            for ancestor in structures[region_id].get("structure_id_path", [])}
        for region_id, region in structures.items():
            if region_id not in visible_ids:
                continue
            item = QTreeWidgetItem([region["name"], region["acronym"]])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            item.setCheckState(0, Qt.Unchecked)
            self.items[region_id] = item
        for region_id, region in structures.items():
            if region_id not in self.items:
                continue
            path = region.get("structure_id_path", [])
            parent_id = path[-2] if len(path) >= 2 else None
            if parent_id in self.items:
                self.items[parent_id].addChild(self.items[region_id])
            else:
                self.tree.addTopLevelItem(self.items[region_id])
        self.nodes = list(self.items.values())
        self.selection_items = {}
        for region_id in available:
            item = self.items[region_id]
            if item.childCount():
                # Some atlases label a parent's own voxels as well as children.
                # Keep these independently selectable instead of re-enabling
                # every child when the direct parent label is selected.
                own = QTreeWidgetItem(["Direct annotation", structures[region_id]["acronym"]])
                own.setFlags(own.flags() | Qt.ItemIsUserCheckable)
                own.setCheckState(0, Qt.Unchecked)
                item.addChild(own)
                self.nodes.append(own)
                item = own
            self.selection_items[region_id] = item
        for region_id in selected_ids:
            if region_id in self.selection_items:
                self.selection_items[region_id].setCheckState(0, Qt.Checked)
        self.tree.expandToDepth(1)
        self.tree.setColumnWidth(0, 420)
        layout.addWidget(self.tree, 1)
        hint = QLabel("Select a parent to include its subregions, or expand it to choose individual regions. "
                      "Apply updates 3D regions and 2D masks.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        if atlas_name == "whs_sd_rat_39um":
            notice = QLabel("Waxholm supplies CA1 / CA2 / CA3 regions, but no separate hippocampal pyramidal-layer mask.")
            notice.setWordWrap(True)
            layout.addWidget(notice)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Apply")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.search.textChanged.connect(self.filter_regions)

    @property
    def selected_ids(self):
        return {region_id for region_id, item in self.selection_items.items()
                if item.checkState(0) == Qt.Checked}

    def select_all(self):
        for index in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(index).setCheckState(0, Qt.Checked)

    def clear_selection(self):
        for index in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(index).setCheckState(0, Qt.Unchecked)

    def filter_regions(self, *_):
        query = self.search.text().casefold().strip()
        visible = set()
        for item in self.nodes:
            text = (item.text(0) + " " + item.text(1)).casefold()
            if query in text:
                descendants = [item]
                while descendants:
                    node = descendants.pop()
                    visible.add(id(node))
                    descendants.extend(node.child(index) for index in range(node.childCount()))
                current = item
                while current is not None:
                    visible.add(id(current))
                    current = current.parent()
        for item in self.nodes:
            item.setHidden(id(item) not in visible)
            if query and id(item) in visible:
                item.setExpanded(True)
