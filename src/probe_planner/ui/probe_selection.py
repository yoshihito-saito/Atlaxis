"""Probe dropdowns and the saved favorite template picker."""

from PySide6.QtCore import QEvent, QPersistentModelIndex, QRect, Qt, Signal
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QHeaderView,
    QLabel, QSizePolicy, QTableWidget, QTableWidgetItem, QToolTip, QVBoxLayout,
    QStyle, QStyledItemDelegate, QStyleOptionViewItem,
)


class RemovableProbeDelegate(QStyledItemDelegate):
    @staticmethod
    def remove_rect(rect):
        return QRect(rect.right() - 27, rect.top(), 24, rect.height())

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setWidth(size.width() + 28)
        size.setHeight(max(size.height(), 27))
        return size

    def paint(self, painter, option, index):
        styled = QStyleOptionViewItem(option)
        self.initStyleOption(styled, index)
        text, styled.text = styled.text, ""
        widget = styled.widget or self.parent()
        widget.style().drawControl(QStyle.CE_ItemViewItem, styled, painter, widget)
        painter.save()
        painter.setFont(styled.font)
        role = QPalette.HighlightedText if styled.state & QStyle.State_Selected else QPalette.Text
        painter.setPen(styled.palette.color(role))
        label_rect = styled.rect.adjusted(6, 0, -32, 0)
        painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter,
                         styled.fontMetrics.elidedText(text, Qt.ElideRight, label_rect.width()))
        painter.drawText(self.remove_rect(styled.rect), Qt.AlignCenter, "×")
        painter.restore()


class ProbeSelector(QComboBox):
    removeRequested = Signal(int)

    def __init__(self, parent=None, *, removable=False):
        super().__init__(parent)
        self.removable = removable
        self._remove_pressed = QPersistentModelIndex()
        self.setMinimumHeight(27)
        self.setMinimumWidth(0)
        self.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setPlaceholderText("Select probe")
        self.setMaxVisibleItems(12)
        self.setToolTipDuration(15000)
        self.currentTextChanged.connect(self.setToolTip)
        if removable:
            self.setItemDelegate(RemovableProbeDelegate(self))
            self.view().installEventFilter(self)
            self.view().viewport().installEventFilter(self)

    def eventFilter(self, watched, event):
        if self.removable and watched is self.view().viewport():
            if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.ToolTip):
                point = event.pos()
                index = self.view().indexAt(point)
                over_remove = (index.isValid() and
                    RemovableProbeDelegate.remove_rect(self.view().visualRect(index)).contains(point))
                if event.type() == QEvent.ToolTip and over_remove:
                    QToolTip.showText(event.globalPos(), f"Remove {index.data()} · Delete", self.view())
                    return True
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    self._remove_pressed = QPersistentModelIndex(index) if over_remove else QPersistentModelIndex()
                    if over_remove:
                        return True
                if (event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton
                        and self._remove_pressed.isValid()):
                    pressed, self._remove_pressed = self._remove_pressed, QPersistentModelIndex()
                    if over_remove and index == pressed:
                        self.hidePopup()
                        self.removeRequested.emit(index.row())
                    return True
        if (self.removable and watched is self.view() and event.type() == QEvent.KeyPress
                and event.key() == Qt.Key_Delete and self.view().isVisible()):
            index = self.view().currentIndex()
            if index.isValid():
                self.hidePopup()
                self.removeRequested.emit(index.row())
            return True
        return super().eventFilter(watched, event)

    def event(self, event):
        if event.type() == QEvent.ToolTip and self.currentIndex() >= 0:
            QToolTip.showText(event.globalPos(), self.currentText(), self)
            return True
        return super().event(event)

    def showPopup(self):
        self._remove_pressed = QPersistentModelIndex()
        text_width = max((self.fontMetrics().horizontalAdvance(self.itemText(i))
                          for i in range(self.count())), default=0)
        width = min(max(self.width(), text_width + 48 + (28 if self.removable else 0)),
                    self.screen().availableGeometry().width() - 40)
        self.view().setMinimumWidth(width)
        super().showPopup()


class FavoriteProbesDialog(QDialog):
    def __init__(self, entries, parent=None):
        super().__init__(parent)
        self.selected_key = None
        self.setWindowTitle("Favorite probes")
        self.resize(640, 360)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Click a probe to load its preview." if entries else
                                "No favorites yet. Select a probe and click ☆ to register it."))
        self.table = QTableWidget(len(entries), 2)
        self.table.setHorizontalHeaderLabels(["Probe", "Headstage"])
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for row, entry in enumerate(sorted(entries, key=lambda entry: entry["name"].casefold())):
            name = QTableWidgetItem(entry["name"])
            name.setData(Qt.UserRole, entry["key"])
            name.setToolTip(entry["name"])
            self.table.setItem(row, 0, name)
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("headstage_id") or "—"))
        self.table.setSortingEnabled(True)
        self.table.cellClicked.connect(self.choose)
        if entries:
            self.table.setCurrentCell(0, 0)
        layout.addWidget(self.table)
        buttons = QDialogButtonBox(QDialogButtonBox.Open | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Open).setText("Load")
        buttons.button(QDialogButtonBox.Open).setEnabled(bool(entries))
        buttons.accepted.connect(lambda: self.choose(self.table.currentRow()))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def choose(self, row, column=0):
        item = self.table.item(row, 0)
        if item is not None:
            self.selected_key = item.data(Qt.UserRole)
            self.accept()
