from PySide6.QtWidgets import (
    QLabel,
    QGridLayout,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.info_card import InfoCard


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titulo = QLabel("Dashboard")

        titulo.setStyleSheet("""
            font-size:32px;
            font-weight:bold;
            padding:20px;
        """)

        layout.addWidget(titulo)

        cards = QGridLayout()

        cards.addWidget(
            InfoCard("Atletas", "0"),
            0,
            0,
        )

        cards.addWidget(
            InfoCard("Treinos Hoje", "0"),
            0,
            1,
        )

        cards.addWidget(
            InfoCard("Próximas Provas", "0"),
            0,
            2,
        )

        cards.addWidget(
            InfoCard("Volume Semana", "0 km"),
            0,
            3,
        )

        layout.addLayout(cards)

        layout.addStretch()