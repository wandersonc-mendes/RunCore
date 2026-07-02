import sys

from PySide6.QtWidgets import QApplication

from config import APP_NAME
from database.database import create_database
from ui.main_window import MainWindow
from models.athlete import Athlete


def main():

    create_database()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()