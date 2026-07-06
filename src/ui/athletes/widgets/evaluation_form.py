from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QSpinBox,
)

from core.physiology.vdot_service import VdotService
from ui.widgets.section_card import SectionCard


class EvaluationForm(SectionCard):

    def __init__(self):
        super().__init__("Dados da Avaliação")

        # ==========================
        # Dados físicos
        # ==========================

        self.weight = QDoubleSpinBox()
        self.weight.setSuffix(" kg")
        self.weight.setDecimals(1)
        self.weight.setRange(20, 250)

        self.height = QDoubleSpinBox()
        self.height.setSuffix(" m")
        self.height.setDecimals(2)
        self.height.setSingleStep(0.01)
        self.height.setRange(0.50, 2.50)

        # ==========================
        # Frequência cardíaca
        # ==========================

        self.max_hr = QSpinBox()
        self.max_hr.setSuffix(" bpm")
        self.max_hr.setRange(50, 250)

        self.resting_hr = QSpinBox()
        self.resting_hr.setSuffix(" bpm")
        self.resting_hr.setRange(20, 120)

        # ==========================
        # Teste
        # ==========================

        self.test_type = QComboBox()
        self.test_type.addItems([
            "1600 m",
            "5 km",
            "10 km",
        ])

        self.distance = QDoubleSpinBox()
        self.distance.setSuffix(" m")
        self.distance.setRange(100, 50000)
        self.distance.setDecimals(0)
        self.distance.setValue(1600)

        self.time_seconds = QSpinBox()
        self.time_seconds.setSuffix(" s")
        self.time_seconds.setRange(1, 30000)

        # ==========================
        # Layout
        # ==========================

        self.add_widget(QLabel("Peso"))
        self.add_widget(self.weight)

        self.add_widget(QLabel("Altura"))
        self.add_widget(self.height)

        self.add_widget(QLabel("FC Máxima"))
        self.add_widget(self.max_hr)

        self.add_widget(QLabel("FC Repouso"))
        self.add_widget(self.resting_hr)

        self.add_widget(QLabel("Tipo de Teste"))
        self.add_widget(self.test_type)

        self.add_widget(QLabel("Distância"))
        self.add_widget(self.distance)

        self.add_widget(QLabel("Tempo"))
        self.add_widget(self.time_seconds)

    def set_evaluation(self, evaluation):

        self.weight.setValue(evaluation.weight)
        self.height.setValue(evaluation.height)
        self.max_hr.setValue(evaluation.max_hr)
        self.resting_hr.setValue(evaluation.resting_hr)

        self.test_type.setCurrentText(
            evaluation.test_type
        )

        self.distance.setValue(
            evaluation.distance
        )

        self.time_seconds.setValue(
            int(evaluation.time_seconds)
        )

    def get_data(self):

        vdot = VdotService.calculate(
            self.distance.value(),
            self.time_seconds.value(),
        )

        return {
            "weight": self.weight.value(),
            "height": self.height.value(),
            "max_hr": self.max_hr.value(),
            "resting_hr": self.resting_hr.value(),
            "test_type": self.test_type.currentText(),
            "distance": self.distance.value(),
            "time_seconds": self.time_seconds.value(),
            "vdot": vdot,
        }