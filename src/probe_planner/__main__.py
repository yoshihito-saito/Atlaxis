import os
import sys


def main():
    os.environ["QT_API"] = "pyside6"
    from PySide6.QtWidgets import QApplication
    from probe_planner.ui.main_window import MainWindow

    application = QApplication(sys.argv)
    application.setApplicationName("Atlaxis Probe Planner")
    application.setOrganizationName("Atlaxis")
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
