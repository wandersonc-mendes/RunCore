from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from repositories.evaluation_repository import (
    EvaluationRepository,
)

from ui.athletes.widgets.evaluation_form import (
    EvaluationForm,
)


class NewEvaluationDialog(QDialog):

    def __init__(
        self,
        athlete,
        evaluation=None,
    ):
        super().__init__()

        self.athlete = athlete
        self.evaluation = evaluation

        self.repository = EvaluationRepository()

        self.setWindowTitle(
            "Nova Avaliação"
            if evaluation is None
            else "Editar Avaliação"
        )

        self.resize(520, 650)

        layout = QVBoxLayout(self)

        self.form = EvaluationForm()

        layout.addWidget(self.form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.btn_save = QPushButton("Salvar")
        self.btn_cancel = QPushButton("Cancelar")

        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_cancel)

        layout.addLayout(buttons)

        self.btn_cancel.clicked.connect(
            self.reject
        )

        self.btn_save.clicked.connect(
            self.save
        )

        if self.evaluation is not None:
            self.form.set_evaluation(
                self.evaluation
            )

    def save(self):

        data = self.form.get_data()

        if self.evaluation is None:

            self.repository.create(
                athlete_id=self.athlete.id,
                **data,
            )

        else:

            self.evaluation.weight = data["weight"]
            self.evaluation.height = data["height"]
            self.evaluation.max_hr = data["max_hr"]
            self.evaluation.resting_hr = data["resting_hr"]
            self.evaluation.test_type = data["test_type"]
            self.evaluation.distance = data["distance"]
            self.evaluation.time_seconds = data["time_seconds"]
            self.evaluation.vdot = data["vdot"]

            self.repository.update(
                self.evaluation
            )

        self.accept()