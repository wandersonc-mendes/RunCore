from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class InfoCard(QFrame):

    def __init__(self, titulo: str, valor: str):
        super().__init__()

        self.setMinimumSize(180, 120)

        self.setStyleSheet("""
            QFrame{
                background:white;
                border:1px solid #d8d8d8;
                border-radius:10px;
            }
        """)

        layout = QVBoxLayout(self)

        titulo_label = QLabel(titulo)
        titulo_label.setAlignment(Qt.AlignCenter)

        titulo_label.setStyleSheet("""
            font-size:14px;
            color:#666666;
        """)

        valor_label = QLabel(valor)
        valor_label.setAlignment(Qt.AlignCenter)

        valor_label.setStyleSheet("""
            font-size:32px;
            font-weight:bold;
        """)

        layout.addWidget(titulo_label)
        layout.addStretch()
        layout.addWidget(valor_label)
        layout.addStretch()