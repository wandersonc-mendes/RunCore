from datetime import datetime, time

from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
)

from repositories.training_session_repository import (
    TrainingSessionRepository,
)


class WorkoutExecutionDialog(QDialog):

    def __init__(self, session):
        super().__init__()

        self.session = session
        self.repository = (
            TrainingSessionRepository()
        )

        self.setWindowTitle(
            "Registrar Execução"
        )

        self.resize(420, 380)

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel(
                f"<h2>{session.workout_name}</h2>"
            )
        )

        form = QFormLayout()

        self.edt_distance = QDoubleSpinBox()
        self.edt_distance.setDecimals(3)
        self.edt_distance.setMaximum(999.999)
        self.edt_distance.setSuffix(" km")
        self.edt_distance.setValue(
            session.completed_distance
        )

        self.edt_duration = QTimeEdit()
        self.edt_duration.setDisplayFormat(
            "HH:mm:ss"
        )

        seconds = session.completed_duration

        self.edt_duration.setTime(
            time(
                hour=seconds // 3600,
                minute=(seconds % 3600) // 60,
                second=seconds % 60,
            )
        )

        self.edt_rpe = QSpinBox()
        self.edt_rpe.setRange(0, 10)
        self.edt_rpe.setValue(
            session.rpe
        )

        self.edt_notes = QTextEdit()
        self.edt_notes.setPlainText(
            session.notes
        )

        form.addRow(
            "Distância",
            self.edt_distance,
        )

        form.addRow(
            "Tempo",
            self.edt_duration,
        )

        form.addRow(
            "RPE",
            self.edt_rpe,
        )

        form.addRow(
            "Observações",
            self.edt_notes,
        )

        layout.addLayout(form)

        buttons = QHBoxLayout()

        btn_cancel = QPushButton(
            "Cancelar"
        )

        btn_save = QPushButton(
            "Salvar"
        )

        btn_cancel.clicked.connect(
            self.reject
        )

        btn_save.clicked.connect(
            self.save
        )

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def save(self):

        self.session.completed = True

        if self.session.completed_at is None:
            self.session.completed_at = (
                datetime.now()
            )

        self.session.completed_distance = (
            self.edt_distance.value()
        )

        t = self.edt_duration.time()

        self.session.completed_duration = (
            t.hour() * 3600
            + t.minute() * 60
            + t.second()
        )

        self.session.rpe = (
            self.edt_rpe.value()
        )

        self.session.notes = (
            self.edt_notes.toPlainText().strip()
        )

        self.repository.update(
            self.session
        )

        self.accept()