from PySide6.QtWidgets import QLabel

from core.training.training_plan_service import (
    TrainingPlanService,
)
from ui.widgets.section_card import SectionCard


class TrainingWeekWidget(SectionCard):

    def __init__(self):
        super().__init__("Semana 1")

        self.labels = []

    def clear(self):

        for label in self.labels:
            label.deleteLater()

        self.labels.clear()

    def load(self, vdot: float):

        self.clear()

        week = TrainingPlanService.generate_base_week(vdot)

        for day in week.days:

            workout = day.workouts[0] if day.workouts else None

            text = f"<b>{day.day}</b>"

            if workout:

                text += f"<br>{workout.name}"

                if workout.distance:
                    text += f" • {workout.distance:.1f} km"

                if workout.repetitions:
                    text += f" • {workout.repetitions}x"

                if workout.recovery:
                    text += f" • Rec: {workout.recovery} m"

            if day.notes:
                text += f"<br><span style='color:#888'>{day.notes}</span>"

            label = QLabel(text)
            label.setWordWrap(True)

            self.labels.append(label)
            self.add_widget(label)

        self.add_stretch()