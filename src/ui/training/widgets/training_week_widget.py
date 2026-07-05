from PySide6.QtWidgets import QLabel

from ui.widgets.section_card import SectionCard

from core.training.training_plan_service import (
    TrainingPlanService,
)


class TrainingWeekWidget(SectionCard):

    def __init__(self):
        super().__init__("Semana 1")

        self.labels = []

        self.load()

    def load(self):

        week = TrainingPlanService.generate_base_week(
            vdot=50
        )

        for day in week.days:

            text = f"{day.day}"

            if day.workouts:

                workout = day.workouts[0]

                text += (
                    f" • {workout.name}"
                )

                if workout.distance:
                    text += (
                        f" - {workout.distance} km"
                    )

            if day.notes:
                text += (
                    f" | {day.notes}"
                )

            label = QLabel(text)

            self.labels.append(label)

            self.add_widget(label)

        self.add_stretch()