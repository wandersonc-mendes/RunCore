from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from theme import BACKGROUND, PAGE_MARGIN

from repositories.athlete_repository import AthleteRepository
from ui.athletes.dialogs.new_athlete_dialog import NewAthleteDialog
from ui.widgets.primary_button import PrimaryButton
from ui.widgets.search_box import SearchBox
from ui.widgets.top_bar import TopBar


class AthletesPage(QWidget):

    def __init__(self):
        super().__init__()

        self.repository = AthleteRepository()

        self.setStyleSheet(f"""
            background: {BACKGROUND};
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            PAGE_MARGIN,
            PAGE_MARGIN,
            PAGE_MARGIN,
            PAGE_MARGIN,
        )

        layout.setSpacing(15)

        layout.addWidget(
            TopBar("Atletas")
        )

        barra = QHBoxLayout()

        self.search = SearchBox()

        self.btn_new = PrimaryButton("+ Novo Atleta")

        barra.addWidget(self.search)
        barra.addWidget(self.btn_new)

        layout.addLayout(barra)

        self.table = QTableWidget()

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(
            [
                "Nome",
                "Objetivo",
                "Status",
            ]
        )

        header = self.table.horizontalHeader()

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

        layout.addWidget(self.table)

        self.btn_new.clicked.connect(
            self.open_new_athlete_dialog
        )

        self.load_athletes()

    def load_athletes(self):

        athletes = self.repository.list_all()

        self.table.setRowCount(len(athletes))

        for row, athlete in enumerate(athletes):

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(athlete.name),
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(athlete.goal),
            )

            status = "Ativo" if athlete.active else "Inativo"

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(status),
            )

    def open_new_athlete_dialog(self):

        dialog = NewAthleteDialog()

        if dialog.exec():

            self.load_athletes()