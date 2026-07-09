from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)

from core.education.workout_knowledge import (
    WorkoutKnowledge,
)
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

        title = QLabel(
            f"<b>{WEEKDAY.get(session.weekday, '')}</b>"
        )

        workout_name = QLabel(
            self.display_name()
        )

        knowledge = (
            WorkoutKnowledge.get(
                session.workout_name
            ) or {}
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
        layout.addWidget(workout_name)
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

        WorkoutDetailsDialog(
            self.session
        ).exec()

        super().mousePressEvent(event)