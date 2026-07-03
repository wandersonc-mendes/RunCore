from PySide6.QtWidgets import (
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

        self.personal_card = SectionCard("Dados pessoais")

        self.phone = InfoItem("Telefone")
        self.email = InfoItem("E-mail")

        self.personal_card.add_widget(self.phone)
        self.personal_card.add_widget(self.email)

        layout.addWidget(self.personal_card)

        self.sport_card = SectionCard("Dados esportivos")

        self.goal = InfoItem("Objetivo")
        self.status = InfoItem("Status")

        self.sport_card.add_widget(self.goal)
        self.sport_card.add_widget(self.status)

        layout.addWidget(self.sport_card)

        self.notes_card = SectionCard("Observações")

        self.notes = InfoItem("")

        self.notes_card.add_widget(self.notes)

        layout.addWidget(self.notes_card)

        layout.addStretch()

    def set_athlete(self, athlete):

        self.phone.set_value(athlete.phone)
        self.email.set_value(athlete.email)

        self.goal.set_value(athlete.goal)
        self.status.set_value(
            "Ativo" if athlete.active else "Inativo"
        )

        self.notes.set_value(athlete.notes)