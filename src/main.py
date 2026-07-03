import sys

from PySide6.QtWidgets import QApplication

from config import APP_NAME
from database.database import create_database

# Registra todos os models
import models

from ui.main_window import MainWindow


def main():

    create_database()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()