from PySide6.QtWidgets import QLabel

from core.training.training_cycle_builder import (
    TrainingCycleBuilder,
)
from ui.training.widgets.workout_card import (
    WorkoutCard,
)
from ui.widgets.section_card import SectionCard


class TrainingWeekWidget(SectionCard):

    def __init__(self):
        super().__init__("Planejamento")

        self.widgets = []

    def clear(self):

        for widget in self.widgets:
            widget.deleteLater()

        self.widgets.clear()

    def load(self, vdot: float):

        self.clear()

        cycle = TrainingCycleBuilder.base(vdot)

        self.title.setText(
            f"Ciclo - {cycle.name}"
        )

        for week in cycle.weeks:

            title = QLabel(
                f"<h3>Semana {week.number}</h3>"
            )

            self.add_widget(title)
            self.widgets.append(title)

            for day in week.days:

                workout = (
                    day.workouts[0]
                    if day.workouts
                    else None
                )

                if workout is None:

                    label = QLabel(
                        f"<b>{day.day}</b><br>Descanso"
                    )

                    label.setWordWrap(True)

                    self.add_widget(label)
                    self.widgets.append(label)

                    continue

                card = WorkoutCard(
                    day,
                    workout,
                )

                self.add_widget(card)
                self.widgets.append(card)

        self.add_stretch()