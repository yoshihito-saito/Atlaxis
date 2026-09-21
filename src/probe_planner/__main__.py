import os
from pathlib import Path
import sys

import probe_planner


def main():
    from multiprocessing import freeze_support
    freeze_support()
    os.environ["QT_API"] = "pyside6"
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
    from probe_planner.ui.storage_dialog import initialize_storage
    from probe_planner.ui.style import STYLE

    application = QApplication(sys.argv)
    application.setApplicationName("Atlaxis Probe Planner")
    application.setOrganizationName("Atlaxis")
    package = Path(probe_planner.__file__).resolve().parent
    icon = package / "data" / "Atlaxis.png"
    if not icon.is_file():
        icon = package.parents[1] / "logo" / "Atlaxis.png"
    application.setWindowIcon(QIcon(str(icon)))
    application.setStyleSheet(STYLE)
    application.setQuitOnLastWindowClosed(False)
    if not initialize_storage():
        return 0
    from probe_planner.ui.main_window import MainWindow

    window = MainWindow()
    window.show()
    application.setQuitOnLastWindowClosed(True)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
