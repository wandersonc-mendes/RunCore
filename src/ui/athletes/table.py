from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
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
            QAbstractItemView.SelectRows
        )

        self.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.setSortingEnabled(True)

    def load(self, athletes: list[Athlete]):

        self.setSortingEnabled(False)

        self.athletes = athletes

        self.setRowCount(len(athletes))

        for row, athlete in enumerate(athletes):

            item_name = QTableWidgetItem(athlete.name)
            item_goal = QTableWidgetItem(athlete.goal)
            item_status = QTableWidgetItem(
                "Ativo" if athlete.active else "Inativo"
            )

            item_name.setData(Qt.UserRole, athlete.id)

            self.setItem(row, 0, item_name)
            self.setItem(row, 1, item_goal)
            self.setItem(row, 2, item_status)

        self.setSortingEnabled(True)

    def selected_athlete(self):

        row = self.currentRow()

        if row < 0:
            return None

        athlete_id = self.item(row, 0).data(Qt.UserRole)

        for athlete in self.athletes:

            if athlete.id == athlete_id:
                return athlete

        return None