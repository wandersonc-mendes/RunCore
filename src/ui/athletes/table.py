from PySide6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from models.athlete import Athlete


class AthletesTable(QTableWidget):

    def __init__(self):
        super().__init__()

        self.athletes = []

        self.setColumnCount(3)

        self.setHorizontalHeaderLabels(
            [
                "Nome",
                "Objetivo",
                "Status",
            ]
        )

        header = self.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )

        self.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.setSelectionMode(
            QTableWidget.SingleSelection
        )

    def load(self, athletes: list[Athlete]):

        self.athletes = athletes

        self.setRowCount(len(athletes))

        for row, athlete in enumerate(athletes):

            self.setItem(
                row,
                0,
                QTableWidgetItem(athlete.name),
            )

            self.setItem(
                row,
                1,
                QTableWidgetItem(athlete.goal),
            )

            self.setItem(
                row,
                2,
                QTableWidgetItem(
                    "Ativo" if athlete.active else "Inativo"
                ),
            )

    def selected_athlete(self):

        row = self.currentRow()

        if row < 0:
            return None

        return self.athletes[row]