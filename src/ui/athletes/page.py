from PySide6.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

from theme import BACKGROUND, PAGE_MARGIN

from repositories.athlete_repository import AthleteRepository
from ui.athletes.dialogs.new_athlete_dialog import NewAthleteDialog
from ui.athletes.table import AthletesTable
from ui.athletes.toolbar import AthletesToolbar
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

        self.toolbar = AthletesToolbar()

        layout.addWidget(self.toolbar)

        self.table = AthletesTable()

        layout.addWidget(self.table)

        self.toolbar.btn_new.clicked.connect(
            self.open_new_athlete_dialog
        )

        self.table.doubleClicked.connect(
            self.edit_selected_athlete
        )

        self.load_athletes()

    def load_athletes(self):

        athletes = self.repository.list_all()

        self.table.load(athletes)

    def open_new_athlete_dialog(self):

        dialog = NewAthleteDialog()

        if dialog.exec():

            self.load_athletes()

    def edit_selected_athlete(self):

        athlete = self.table.selected_athlete()

        if athlete is None:
            return

        dialog = NewAthleteDialog(athlete)

        if dialog.exec():

            self.load_athletes()