from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.education.workout_knowledge import (
    WorkoutKnowledge,
)
from ui.training.dialogs.workout_execution_dialog import (
    WorkoutExecutionDialog,
)


class WorkoutDetailsDialog(QDialog):

    def __init__(self, session):
        super().__init__()

        self.session = session

        self.setWindowTitle(
            session.workout_name
        )

        self.resize(520, 560)

        layout = QVBoxLayout(self)

        knowledge = (
            WorkoutKnowledge.get(
                session.workout_name
            ) or {}
        )

        layout.addWidget(
            QLabel(
                f"<h2>{session.workout_name}</h2>"
            )
        )

        if session.repetitions:

            info = (
                f"{session.repetitions} × "
                f"{int(session.planned_distance)} m"
            )

        else:

            info = (
                f"{session.planned_distance:.3f} km"
            )

        layout.addWidget(
            QLabel(
                f"<b>Sessão</b><br>{info}"
            )
        )

        layout.addWidget(
            QLabel(
                f"<b>Zona</b><br>{session.zone}"
            )
        )

        layout.addWidget(
            QLabel(
                "<b>Objetivo</b><br>"
                + knowledge.get(
                    "objective",
                    "-",
                )
            )
        )

        layout.addWidget(
            QLabel(
                "<b>Adaptações</b><br>"
                + "<br>".join(
                    f"• {i}"
                    for i in knowledge.get(
                        "adaptations",
                        [],
                    )
                )
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

        layout.addWidget(
            QLabel(
                "<b>Erros comuns</b><br>"
                + "<br>".join(
                    f"• {i}"
                    for i in knowledge.get(
                        "errors",
                        [],
                    )
                )
            )
        )

        if session.completed:

            h = session.completed_duration // 3600
            m = (
                session.completed_duration % 3600
            ) // 60
            s = (
                session.completed_duration % 60
            )

            execution = f"""
<b>Execução</b><br>
✓ {session.completed_distance:.3f} km<br>
⏱ {h:02}:{m:02}:{s:02}<br>
RPE: {session.rpe}
"""

            if session.notes:

                execution += (
                    "<br>Observações:<br>"
                    + session.notes
                )

            layout.addWidget(
                QLabel(execution)
            )

        status = (
            "🟢 Concluído"
            if session.completed
            else "🟡 Pendente"
        )

        layout.addWidget(
            QLabel(
                f"<b>Status</b><br>{status}"
            )
        )

        layout.addStretch()

        btn_execution = QPushButton(
            "Registrar Execução"
            if not session.completed
            else "Editar Execução"
        )

        btn_execution.clicked.connect(
            self.open_execution
        )

        layout.addWidget(
            btn_execution
        )

        btn_close = QPushButton(
            "Fechar"
        )

        btn_close.clicked.connect(
            self.accept
        )

        layout.addWidget(
            btn_close
        )

    def open_execution(self):

        dialog = WorkoutExecutionDialog(
            self.session
        )

        if dialog.exec():
            self.accept()