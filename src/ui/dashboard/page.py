from PySide6.QtWidgets import (
    QGridLayout,
    QVBoxLayout,
    QWidget,
)

from theme import (
    BACKGROUND,
    PAGE_MARGIN,
)

from ui.widgets.info_card import InfoCard
from ui.widgets.top_bar import TopBar


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setStyleSheet(f"""
            background:{BACKGROUND};
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            PAGE_MARGIN,
            PAGE_MARGIN,
            PAGE_MARGIN,
            PAGE_MARGIN,
        )

        layout.addWidget(
            TopBar("Dashboard")
        )

        cards = QGridLayout()

        cards.setHorizontalSpacing(18)
        cards.setVerticalSpacing(18)

        cards.addWidget(
            InfoCard("👥 Atletas", "0"),
            0,
            0,
        )

        cards.addWidget(
            InfoCard("🏃 Treinos Hoje", "0"),
            0,
            1,
        )

        cards.addWidget(
            InfoCard("🏁 Próximas Provas", "0"),
            0,
            2,
        )

        cards.addWidget(
            InfoCard("📈 Volume Semanal", "0 km"),
            0,
            3,
        )

        layout.addLayout(cards)

        layout.addStretch()