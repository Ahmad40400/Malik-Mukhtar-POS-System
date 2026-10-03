# main.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app.database import init_db
from app.ui.main_window import MainWindow


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("Retail POS")
    app.setStyle("Fusion")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()