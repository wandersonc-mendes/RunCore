from PySide6.QtWidgets import (
    QGridLayout,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.info_item import InfoItem
from ui.widgets.section_card import SectionCard


class AthleteGeneralTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(15)

        grid = QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(15)

        layout.addLayout(grid)

        # ==========================
        # Dados pessoais
        # ==========================

        self.personal_card = SectionCard("Dados pessoais")

        self.phone = InfoItem("Telefone")
        self.email = InfoItem("E-mail")

        self.personal_card.add_widget(self.phone)
        self.personal_card.add_widget(self.email)
        self.personal_card.add_stretch()

        # ==========================
        # Dados esportivos
        # ==========================

        self.sport_card = SectionCard("Dados esportivos")

        self.goal = InfoItem("Objetivo")
        self.status = InfoItem("Status")

        self.sport_card.add_widget(self.goal)
        self.sport_card.add_widget(self.status)
        self.sport_card.add_stretch()

        grid.addWidget(self.personal_card, 0, 0)
        grid.addWidget(self.sport_card, 0, 1)

        # ==========================
        # Observações
        # ==========================

        self.notes_card = SectionCard("Observações")

        self.notes = InfoItem("")

        self.notes_card.add_widget(self.notes)

        layout.addWidget(self.notes_card)

    def set_athlete(self, athlete):

        self.phone.set_value(athlete.phone)
        self.email.set_value(athlete.email)

        self.goal.set_value(athlete.goal)

        self.status.set_value(
            "Ativo" if athlete.active else "Inativo"
        )

        self.notes.set_value(athlete.notes)