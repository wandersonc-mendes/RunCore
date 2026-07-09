from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)

from core.education.workout_knowledge import (
    WorkoutKnowledge,
)
from core.training.workout import Workout
from ui.training.dialogs.workout_details_dialog import (
    WorkoutDetailsDialog,
)


WEEKDAY = {
    0: "Segunda",
    1: "Terça",
    2: "Quarta",
    3: "Quinta",
    4: "Sexta",
    5: "Sábado",
    6: "Domingo",
}


class WorkoutCard(QFrame):

    def __init__(self, session):
        super().__init__()

        self.session = session

        self.setObjectName("WorkoutCard")

        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
            QFrame#WorkoutCard{
                border:1px solid #D9D9D9;
                border-radius:8px;
                background:white;
                padding:8px;
            }

            QFrame#WorkoutCard:hover{
                border:1px solid #1E88E5;
                background:#F8FBFF;
            }
        """)

        layout = QVBoxLayout(self)

        knowledge = (
            WorkoutKnowledge.get(
                session.workout_name
            ) or {}
        )

        title = QLabel(
            f"<b>{WEEKDAY.get(session.weekday, '')}</b>"
        )

        workout = QLabel(
            self.display_name()
        )

        objective = QLabel(
            knowledge.get(
                "objective",
                "",
            )
        )

        objective.setStyleSheet(
            "color:#666;"
        )

        layout.addWidget(title)
        layout.addWidget(workout)
        layout.addWidget(objective)

    def display_name(self):

        if self.session.repetitions:

            return (
                f"{self.session.workout_name} - "
                f"{self.session.repetitions} × "
                f"{int(self.session.distance)} m"
            )

        return (
            f"{self.session.workout_name} - "
            f"{self.session.distance:.1f} km"
        )

    def mousePressEvent(self, event):

        workout = Workout(
            name=self.session.workout_name,
            zone=self.session.zone,
            distance=(
                self.session.distance
                if self.session.distance > 0
                else None
            ),
            repetitions=(
                self.session.repetitions
                if self.session.repetitions > 0
                else None
            ),
            recovery=(
                self.session.recovery
                if self.session.recovery > 0
                else None
            ),
        )

        WorkoutDetailsDialog(
            workout
        ).exec()

        super().mousePressEvent(event)