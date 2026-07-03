from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from repositories.evaluation_repository import EvaluationRepository
from ui.widgets.section_card import SectionCard


class NewEvaluationDialog(QDialog):

    def __init__(self, athlete):
        super().__init__()

        self.athlete = athlete
        self.repository = EvaluationRepository()

        self.setWindowTitle("Nova Avaliação")
        self.resize(520, 520)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # ==================================================
        # Dados físicos
        # ==================================================

        physical = SectionCard("Dados físicos")

        self.weight = QDoubleSpinBox()
        self.weight.setSuffix(" kg")
        self.weight.setDecimals(1)
        self.weight.setRange(20, 250)

        self.height = QDoubleSpinBox()
        self.height.setSuffix(" m")
        self.height.setDecimals(2)
        self.height.setSingleStep(0.01)
        self.height.setRange(0.50, 2.50)

        physical.add_widget(QLabel("Peso"))
        physical.add_widget(self.weight)

        physical.add_widget(QLabel("Altura"))
        physical.add_widget(self.height)

        # ==================================================
        # Frequência Cardíaca
        # ==================================================

        heart = SectionCard("Frequência Cardíaca")

        self.max_hr = QSpinBox()
        self.max_hr.setSuffix(" bpm")
        self.max_hr.setRange(50, 250)

        self.resting_hr = QSpinBox()
        self.resting_hr.setSuffix(" bpm")
        self.resting_hr.setRange(20, 120)

        heart.add_widget(QLabel("FC Máxima"))
        heart.add_widget(self.max_hr)

        heart.add_widget(QLabel("FC Repouso"))
        heart.add_widget(self.resting_hr)

        # ==================================================
        # Performance
        # ==================================================

        performance = SectionCard("Performance")

        self.vo2 = QDoubleSpinBox()
        self.vo2.setDecimals(1)
        self.vo2.setRange(10, 100)

        performance.add_widget(QLabel("VO₂ Máx"))
        performance.add_widget(self.vo2)

        # ==================================================

        layout.addWidget(physical)
        layout.addWidget(heart)
        layout.addWidget(performance)

        layout.addStretch()

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.btn_save = QPushButton("Salvar")
        self.btn_cancel = QPushButton("Cancelar")

        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_cancel)

        layout.addLayout(buttons)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.save)

        self.cancel = self.btn_cancel
        self.save_button = self.btn_save

        self.cancel.setAutoDefault(False)
        self.cancel.setDefault(False)

        self.save_button.setAutoDefault(True)
        self.save_button.setDefault(True)

    def save(self):

        self.repository.create(
            athlete_id=self.athlete.id,
            weight=self.weight.value(),
            height=self.height.value(),
            max_hr=self.max_hr.value(),
            resting_hr=self.resting_hr.value(),
            vo2=self.vo2.value(),
        )

        self.accept()