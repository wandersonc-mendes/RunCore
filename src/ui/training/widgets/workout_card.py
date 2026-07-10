from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
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


ZONE_COLOR = {
    "Easy": "#43A047",
    "Marathon": "#1E88E5",
    "Threshold": "#FB8C00",
    "Interval": "#E53935",
    "Repetition": "#8E24AA",
}


class WorkoutCard(QFrame):

    def __init__(
        self,
        session,
        reload_callback=None,
    ):
        super().__init__()

        self.session = session
        self.reload_callback = reload_callback

        self.setObjectName("WorkoutCard")
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
            QFrame#WorkoutCard{
                border:1px solid #D9D9D9;
                border-radius:8px;
                background:white;
                padding:10px;
            }

            QFrame#WorkoutCard:hover{
                border:1px solid #1976D2;
                background:#F8FBFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        header = QHBoxLayout()

        day = QLabel(
            f"<b>{WEEKDAY.get(session.weekday,'')}</b>"
        )

        status = QLabel(
            "CONCLUÍDO"
            if session.completed
            else "PENDENTE"
        )

        status.setAlignment(Qt.AlignCenter)
        status.setFixedWidth(95)

        status.setStyleSheet(f"""
            QLabel{{
                background:{
                    "#2E7D32"
                    if session.completed
                    else "#F9A825"
                };
                color:white;
                border-radius:8px;
                padding:4px;
                font-weight:bold;
                font-size:10px;
            }}
        """)

        header.addWidget(day)
        header.addStretch()
        header.addWidget(status)

        layout.addLayout(header)

        info = QHBoxLayout()

        zone = QLabel(session.zone.upper())

        zone.setAlignment(Qt.AlignCenter)
        zone.setFixedWidth(80)

        zone.setStyleSheet(f"""
            QLabel{{
                background:{
                    ZONE_COLOR.get(
                        session.zone,
                        "#757575"
                    )
                };
                color:white;
                border-radius:8px;
                padding:3px;
                font-size:10px;
                font-weight:bold;
            }}
        """)

        workout = QLabel(
            self.display_name()
        )

        workout.setStyleSheet("""
            font-weight:bold;
        """)

        info.addWidget(zone)
        info.addSpacing(8)
        info.addWidget(workout)
        info.addStretch()

        layout.addLayout(info)

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

        objective.setWordWrap(True)
        objective.setStyleSheet("""
            color:#666666;
        """)

        layout.addWidget(objective)

        if session.completed:

            h = session.completed_duration // 3600
            m = (
                session.completed_duration % 3600
            ) // 60
            s = (
                session.completed_duration % 60
            )

            execution = QLabel(
                f"✓ {session.completed_distance:.3f} km    "
                f"⏱ {h:02}:{m:02}:{s:02}"
            )

            execution.setStyleSheet("""
                color:#2E7D32;
                font-weight:bold;
            """)

            layout.addWidget(execution)

    def display_name(self):

        if self.session.repetitions:

            return (
                f"{self.session.workout_name} • "
                f"{self.session.repetitions} × "
                f"{int(self.session.planned_distance)} m"
            )

        return (
            f"{self.session.workout_name} • "
            f"{self.session.planned_distance:.3f} km"
        )

    def mousePressEvent(self, event):

        dialog = WorkoutDetailsDialog(
            self.session
        )

        result = dialog.exec()

        if (
            result == dialog.DialogCode.Accepted
            and self.reload_callback
        ):
            self.reload_callback()

        super().mousePressEvent(event)