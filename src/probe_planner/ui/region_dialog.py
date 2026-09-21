"""Select existing atlas annotations; no custom segmentation or relabeling."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QLabel, QDialogButtonBox, QPushButton,
)
from probe_planner.atlas.regions import brain_region_ids


def populate_region_tree(tree, structures, available_ids=None):
    allowed = brain_region_ids(structures)
    available = allowed & set(structures if available_ids is None else available_ids)
    visible = (available | {ancestor for rid in available
               for ancestor in structures[rid].get("structure_id_path", [])}) & allowed
    items = {}
    for rid, region in structures.items():
        if rid in visible:
            item = QTreeWidgetItem([region["name"], region["acronym"]])
            item.setData(0, Qt.UserRole, rid)
            item.setToolTip(0, region["name"])
            items[rid] = item
    for rid, item in items.items():
        path = structures[rid].get("structure_id_path", [])
        parent_id = path[-2] if len(path) >= 2 else None
        if parent_id in items:
            items[parent_id].addChild(item)
        else:
            tree.addTopLevelItem(item)
    return items, available


def filter_region_tree(nodes, query):
    query = query.casefold().strip()
    visible = set()
    for item in nodes:
        if query in (item.text(0) + " " + item.text(1)).casefold():
            descendants = [item]
            while descendants:
                node = descendants.pop()
                visible.add(id(node))
                descendants.extend(node.child(index) for index in range(node.childCount()))
            current = item
            while current is not None:
                visible.add(id(current))
                current = current.parent()
    for item in nodes:
        item.setHidden(id(item) not in visible)
        if query and id(item) in visible:
            item.setExpanded(True)


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
        self.items, available = populate_region_tree(self.tree, structures, available_ids)
        for item in self.items.values():
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            item.setCheckState(0, Qt.Unchecked)
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
        filter_region_tree(self.nodes, self.search.text())


class RegionSelectionDialog(QDialog):
    """Choose a union of ROI regions, each including its descendants."""

    def __init__(self, structures, region_ids, parent=None, available_ids=None):
        super().__init__(parent)
        self.setWindowTitle("Channel selection regions")
        self.resize(620, 540)
        self.selected_region_ids = None if region_ids is None else list(region_ids)
        layout = QVBoxLayout(self)
        search = QLineEdit()
        search.setPlaceholderText("Search name or acronym")
        layout.addWidget(search)
        actions = QHBoxLayout()
        all_regions = QPushButton("All Brain regions")
        all_regions.clicked.connect(self.select_brain)
        actions.addWidget(all_regions)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear_selection)
        actions.addWidget(clear)
        actions.addStretch()
        layout.addLayout(actions)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Region / layer", "Acronym"])
        self.items, _ = populate_region_tree(self.tree, structures, available_ids)
        self.tree.setColumnWidth(0, 420)
        self.tree.expandToDepth(1)
        for rid, item in self.items.items():
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked if rid in (region_ids or []) else Qt.Unchecked)
        if region_ids and region_ids[0] in self.items:
            self.tree.setCurrentItem(self.items[region_ids[0]])
            self.tree.scrollToItem(self.items[region_ids[0]])
        layout.addWidget(self.tree)
        hint = QLabel("Check one or more regions. Each checked region includes all its subregions. "
                      "Channels in any checked region are eligible within the drawn ROI.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.apply_button = buttons.button(QDialogButtonBox.Ok)
        self.apply_button.setText("Apply")
        buttons.accepted.connect(self.apply_region)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.tree.itemChanged.connect(self.update_apply)
        self.update_apply()
        search.textChanged.connect(lambda query: filter_region_tree(list(self.items.values()), query))

    def select_brain(self):
        self.selected_region_ids = None
        self.accept()

    def clear_selection(self):
        for item in self.items.values():
            item.setCheckState(0, Qt.Unchecked)

    def update_apply(self, *_):
        self.apply_button.setEnabled(any(item.checkState(0) == Qt.Checked for item in self.items.values()))

    def apply_region(self):
        selected = [rid for rid, item in self.items.items() if item.checkState(0) == Qt.Checked]
        if selected:
            self.selected_region_ids = selected
            self.accept()
