from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from core.physiology.imc_service import ImcService


class EvaluationTable(QTableWidget):

    def __init__(self):
        super().__init__()

        self.setColumnCount(8)

        self.setHorizontalHeaderLabels([
            "Data",
            "Teste",
            "Distância",
            "Peso",
            "IMC",
            "FC Máx",
            "FC Rep.",
            "VDOT",
        ])

        header = self.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.Stretch)

        for column in range(1, 8):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeToContents,
            )

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)

    def load(self, evaluations):

        self.setRowCount(len(evaluations))

        for row, evaluation in enumerate(evaluations):

            imc = ImcService.calculate(
                evaluation.weight,
                evaluation.height,
            )

            self.setItem(row,0,QTableWidgetItem(
                evaluation.created_at.strftime("%d/%m/%Y")
            ))
            self.setItem(row,1,QTableWidgetItem(
                evaluation.test_type
            ))
            self.setItem(row,2,QTableWidgetItem(
                f"{evaluation.distance:.0f} m"
            ))
            self.setItem(row,3,QTableWidgetItem(
                f"{evaluation.weight:.1f} kg"
            ))
            self.setItem(row,4,QTableWidgetItem(
                f"{imc:.1f}"
            ))
            self.setItem(row,5,QTableWidgetItem(
                str(evaluation.max_hr)
            ))
            self.setItem(row,6,QTableWidgetItem(
                str(evaluation.resting_hr)
            ))
            self.setItem(row,7,QTableWidgetItem(
                f"{evaluation.vdot:.1f}"
            ))
