from tkinter import dialog

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.training.training_persistence_service import (
    TrainingPersistenceService,
)
from repositories.athlete_repository import AthleteRepository
from repositories.evaluation_repository import (
    EvaluationRepository,
)
from repositories.training_repository import (
    TrainingRepository,
)

from ui.training.widgets.training_week_widget import (
    TrainingWeekWidget,
)

from ui.training.dialogs.training_structure_dialog import (
    TrainingStructureDialog,
)

class TrainingPage(QWidget):

    def __init__(self):
        super().__init__()

        self.athlete_repository = AthleteRepository()
        self.evaluation_repository = EvaluationRepository()
        self.training_repository = TrainingRepository()
        self.persistence = (
            TrainingPersistenceService()
        )

        layout = QVBoxLayout(self)

        self.title = QLabel("Planejamento de Treinos")
        self.title.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
        """)

        layout.addWidget(self.title)

        self.cmb_athlete = QComboBox()
        layout.addWidget(self.cmb_athlete)

        self.info = QLabel()
        layout.addWidget(self.info)

        self.btn_generate = QPushButton(
            "Gerar Planejamento"
        )
        self.btn_generate.clicked.connect(
            self.generate_training
        )

        self.btn_regenerate = QPushButton(
            "Regenerar Planejamento"
        )
        self.btn_regenerate.clicked.connect(
            self.regenerate_training
        )

        buttons = QHBoxLayout()

        buttons.addWidget(self.btn_generate)
        buttons.addWidget(self.btn_regenerate)

        layout.addLayout(buttons)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(
            QScrollArea.NoFrame
        )

        self.week = TrainingWeekWidget()

        self.week.set_reload_callback(
            self.load_training
        )
        self.scroll.setWidget(
            self.week
        )

        layout.addWidget(
            self.scroll
        )

        self.load_athletes()

        self.cmb_athlete.currentIndexChanged.connect(
            self.load_training
        )

    def load_athletes(self):

        self.cmb_athlete.blockSignals(True)
        self.cmb_athlete.clear()

        athletes = self.athlete_repository.list_all()

        for athlete in athletes:
            self.cmb_athlete.addItem(
                athlete.name,
                athlete.id,
            )

        self.cmb_athlete.blockSignals(False)

        if athletes:
            self.load_training()

    def generate_training(self):

        athlete_id = self.cmb_athlete.currentData()

        if athlete_id is None:
            return

        evaluation = (
            self.evaluation_repository.last_evaluation(
                athlete_id
            )
        )

        if evaluation is None:
            return

        training = (
            self.training_repository.get_active_by_athlete(
                athlete_id
            )
        )

        if training is None:

            self.persistence.create_training(
                athlete_id=athlete_id,
                vdot=evaluation.vdot,
                name="Planejamento Principal",
                methodology="Jack Daniels",
                objective="Desenvolvimento",
                target_distance=42.195,
            )

        self.load_training()

    def regenerate_training(self):

        athlete_id = self.cmb_athlete.currentData()

        if athlete_id is None:
            return

        evaluation = (
            self.evaluation_repository.last_evaluation(
                athlete_id
            )
        )

        if evaluation is None:
            return

        training = (
            self.training_repository.get_active_by_athlete(
                athlete_id
            )
        )

        if training is None:
            return

        self.persistence.regenerate_training(
            training.id,
            evaluation.vdot,
        )

        self.load_training()

    def load_training(self):

        athlete_id = self.cmb_athlete.currentData()

        if athlete_id is None:

            self.info.setText(
                "Nenhum atleta cadastrado."
            )

            self.btn_generate.hide()
            self.btn_regenerate.hide()
            self.week.hide()

            return

        athlete = self.athlete_repository.get_by_id(
            athlete_id
        )

        evaluation = (
            self.evaluation_repository.last_evaluation(
                athlete_id
            )
        )

        self.title.setText(
            f"Planejamento - {athlete.name}"
        )

        if evaluation is None:

            self.info.setText(
                "Atleta sem avaliação."
            )

            self.btn_generate.hide()
            self.btn_regenerate.hide()
            self.week.hide()

            return

        self.info.setText(
            f"VDOT: {evaluation.vdot:.1f}"
        )

        training = (
            self.training_repository.get_active_by_athlete(
                athlete_id
            )
        )

        if training is None:

            self.btn_generate.show()
            self.btn_regenerate.hide()
            self.week.hide()

            return

        self.btn_generate.hide()
        self.btn_regenerate.show()

        self.week.show()
        self.week.load(training.id)