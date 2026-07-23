import sys

from PySide6.QtWidgets import QApplication

from config import APP_NAME
from database.bootstrap import initialize_database

# Registra todos os models
import models

from ui.main_window import MainWindow


def main():

    initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()