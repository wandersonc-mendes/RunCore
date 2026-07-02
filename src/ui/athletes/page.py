from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AthletesPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titulo = QLabel("Atletas")
        titulo.setAlignment(Qt.AlignCenter)

        titulo.setStyleSheet("""
            font-size:32px;
            font-weight:bold;
        """)

        layout.addStretch()
        layout.addWidget(titulo)
        layout.addStretch()