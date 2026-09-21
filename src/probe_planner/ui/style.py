from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QMessageBox


def question(parent, title, text, buttons, default_button):
    """Show a confirmation with a white question mark on the dark background."""
    dialog = QMessageBox(QMessageBox.Question, title, text, buttons, parent)
    dialog.setDefaultButton(default_button)
    icon = dialog.iconPixmap()
    painter = QPainter(icon)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(icon.rect(), Qt.white)
    painter.end()
    dialog.setIconPixmap(icon)
    answer = dialog.exec()
    dialog.deleteLater()
    return answer


STYLE = """
QMainWindow, QWidget { background: #101216; color: #d6dde8; font-size: 11px; }
QToolBar { background: #191e26; border: 0; padding: 4px; spacing: 6px; }
QPushButton, QToolButton { background: #242c39; border: 1px solid #354256;
    padding: 5px 9px; border-radius: 4px; }
QPushButton:hover, QToolButton:hover { background: #33435e; }
QToolButton#addProbe { background: transparent; color: #b8c7da; padding: 0;
    border: 1px solid #2a3442; border-radius: 5px; font-size: 17px; font-weight: 400; }
QToolButton#addProbe:hover { background: #253349; color: #edf3ff; border-color: #527dc9; }
QToolButton#addProbe:pressed { background: #33435e; }
QToolButton#addProbe:focus { border-color: #7aa7ff; }
QToolButton#addProbe:disabled { background: transparent; color: #616977; border-color: #242c39; }
QPushButton#closeProbe { padding: 0; border: 0; background: transparent; }
QPushButton#closeProbe:hover { background: #49556a; }
QToolButton#favoriteProbe { padding: 0; border: 0; background: transparent;
    color: #8a9099; font-size: 16px; }
QToolButton#favoriteProbe:checked { color: #ffd34e; }
QToolButton#favoriteProbe:hover { background: #49556a; }
QPushButton:disabled, QToolButton:disabled { color: #616977; border-color: #242c39; }
QLineEdit, QDoubleSpinBox, QComboBox { background: #191e26; border: 1px solid #354256;
    border-radius: 3px; padding: 4px; selection-background-color: #527dc9; }
QComboBox { padding-right: 22px; }
QComboBox::drop-down { width: 20px; border: 0; }
QGroupBox { border: 1px solid #2a3442; border-radius: 5px;
    margin-top: 10px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #b8c7da; }
QHeaderView::section { background: #242c39; color: #b8c7da; border: 0;
    border-right: 1px solid #354256; padding: 6px; }
QTableWidget { background: #101216; alternate-background-color: #191e26;
    gridline-color: #242c39; selection-background-color: #33435e; }
QSplitter::handle { background: #242c39; }
QTabWidget::pane { border: 1px solid #2a3442; }
QTabBar::tab { background: #191e26; padding: 7px 8px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { background: #242c39; border-bottom-color: #7aa7ff; }
QTabBar::tab:hover { background: #33435e; }
QStackedWidget#probeSummaryPages { border: 1px solid #2a3442; }
QWidget#probePage { border: 1px solid #2a3442; border-radius: 4px; }
QSlider::groove:horizontal { height: 4px; background: #354256; border-radius: 2px; }
QSlider::handle:horizontal { width: 12px; margin: -4px 0; border-radius: 6px; background: #7aa7ff; }
QStatusBar { color: #8a9099; }
QLabel#title { font-size: 19px; font-weight: 600; color: #dfe5ee; }
QLabel#muted { color: #8a9099; }
"""
