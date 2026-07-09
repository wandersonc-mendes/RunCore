from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from repositories.athlete_repository import AthleteRepository
from repositories.evaluation_repository import EvaluationRepository

from ui.training.widgets.training_week_widget import (
    TrainingWeekWidget,
)


class TrainingPage(QWidget):

    def __init__(self):
        super().__init__()

        self.athlete_repository = AthleteRepository()
        self.evaluation_repository = EvaluationRepository()

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

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)

        self.week = TrainingWeekWidget()

        self.scroll.setWidget(self.week)

        layout.addWidget(self.scroll)

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

    def load_training(self):

        athlete_id = self.cmb_athlete.currentData()

        if athlete_id is None:
            self.info.setText("Nenhum atleta cadastrado.")
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

            self.week.hide()

            return

        self.info.setText(
            f"VDOT: {evaluation.vdot:.1f}"
        )

        self.week.show()
        self.week.load(evaluation.vdot)