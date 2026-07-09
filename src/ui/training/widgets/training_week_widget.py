from PySide6.QtWidgets import QLabel

from core.training.training_query_service import (
    TrainingQueryService,
)
from ui.training.widgets.workout_card import (
    WorkoutCard,
)
from ui.widgets.section_card import SectionCard


class TrainingWeekWidget(SectionCard):

    def __init__(self):
        super().__init__("Planejamento")

        self.widgets = []
        self.query = TrainingQueryService()

    def clear(self):

        for widget in self.widgets:
            widget.deleteLater()

        self.widgets.clear()

    def load(self, training_id: int):

        self.clear()

        weeks = self.query.sessions_by_week(
            training_id
        )

        self.title.setText(
            "Planejamento"
        )

        for week_number in sorted(weeks.keys()):

            title = QLabel(
                f"<h3>Semana {week_number}</h3>"
            )

            self.add_widget(title)
            self.widgets.append(title)

            for session in weeks[week_number]:

                card = WorkoutCard(session)

                self.add_widget(card)
                self.widgets.append(card)

        self.add_stretch()