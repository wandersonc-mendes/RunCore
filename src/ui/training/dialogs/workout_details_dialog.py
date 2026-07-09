from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.education.workout_knowledge import (
    WorkoutKnowledge,
)


class WorkoutDetailsDialog(QDialog):

    def __init__(self, workout):
        super().__init__()

        self.setWindowTitle(workout.name)
        self.resize(520, 520)

        layout = QVBoxLayout(self)

        knowledge = (
            WorkoutKnowledge.get(workout.name)
            or {}
        )

        title = QLabel(
            f"<h2>{workout.name}</h2>"
        )

        layout.addWidget(title)

        layout.addWidget(
            QLabel(
                f"<b>Objetivo</b><br>"
                f"{knowledge.get('objective', '-')}"
            )
        )

        adaptations = "<br>".join(
            f"• {item}"
            for item in knowledge.get(
                "adaptations",
                [],
            )
        )

        layout.addWidget(
            QLabel(
                "<b>Adaptações</b><br>"
                + adaptations
            )
        )

        layout.addWidget(
            QLabel(
                "<b>Sensação esperada</b><br>"
                + knowledge.get(
                    "perception",
                    "-",
                )
            )
        )

        errors = "<br>".join(
            f"• {item}"
            for item in knowledge.get(
                "errors",
                [],
            )
        )

        layout.addWidget(
            QLabel(
                "<b>Erros comuns</b><br>"
                + errors
            )
        )

        layout.addStretch()

        btn = QPushButton("Fechar")
        btn.clicked.connect(self.accept)

        layout.addWidget(btn)