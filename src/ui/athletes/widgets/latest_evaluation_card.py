from ui.widgets.info_item import InfoItem
from ui.widgets.section_card import SectionCard

from core.physiology.imc_service import ImcService


class LatestEvaluationCard(SectionCard):

    def __init__(self):
        super().__init__("Última Avaliação")

        self.weight = InfoItem("Peso")
        self.height = InfoItem("Altura")
        self.imc = InfoItem("IMC")
        self.max_hr = InfoItem("FC Máxima")
        self.resting_hr = InfoItem("FC Repouso")
        self.vdot = InfoItem("VDOT")

        self.add_widget(self.weight)
        self.add_widget(self.height)
        self.add_widget(self.imc)
        self.add_widget(self.max_hr)
        self.add_widget(self.resting_hr)
        self.add_widget(self.vdot)

        self.add_stretch()

    def clear(self):

        self.weight.set_value("-")
        self.height.set_value("-")
        self.imc.set_value("-")
        self.max_hr.set_value("-")
        self.resting_hr.set_value("-")
        self.vdot.set_value("-")

    def set_evaluation(self, evaluation):

        if evaluation is None:
            self.clear()
            return

        imc = ImcService.calculate(
            evaluation.weight,
            evaluation.height,
        )

        classification = ImcService.classify(imc)

        if imc < 18.5:
            color = "#3498DB"
        elif imc < 25:
            color = "#2ECC71"
        elif imc < 30:
            color = "#F1C40F"
        elif imc < 35:
            color = "#E67E22"
        else:
            color = "#E74C3C"

        self.weight.set_value(
            f"{evaluation.weight:.1f} kg"
        )

        self.height.set_value(
            f"{evaluation.height:.2f} m"
        )

        self.imc.set_colored_value(
            f"{imc:.1f} ({classification})",
            color,
        )

        self.max_hr.set_value(
            f"{evaluation.max_hr} bpm"
        )

        self.resting_hr.set_value(
            f"{evaluation.resting_hr} bpm"
        )

        self.vdot.set_value(
            f"{evaluation.vdot:.1f}"
        )