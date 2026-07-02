from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from theme import TITLE_SIZE, TEXT, TEXT_SECONDARY


class TopBar(QWidget):

    def __init__(self, title: str):
        super().__init__()

        layout = QVBoxLayout(self)

        titulo = QLabel(title)
        titulo.setStyleSheet(f"""
            font-size:{TITLE_SIZE}px;
            font-weight:bold;
            color:{TEXT};
        """)

        hoje = datetime.now().strftime("%d/%m/%Y")

        subtitulo = QLabel(
            f"Bem-vindo ao RunCore • {hoje}"
        )

        subtitulo.setStyleSheet(f"""
            color:{TEXT_SECONDARY};
            font-size:14px;
        """)

        titulo.setAlignment(Qt.AlignLeft)
        subtitulo.setAlignment(Qt.AlignLeft)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        layout.setSpacing(3)