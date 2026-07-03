from PySide6.QtWidgets import (
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from theme import BACKGROUND, PAGE_MARGIN

from repositories.athlete_repository import AthleteRepository
from ui.athletes.dialogs.new_athlete_dialog import NewAthleteDialog
from ui.athletes.dialogs.athlete_profile_dialog import AthleteProfileDialog
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

        self.toolbar.btn_delete.clicked.connect(
            self.delete_selected_athlete
        )

        self.toolbar.search.textChanged.connect(
            self.search_athletes
        )

        self.table.doubleClicked.connect(
            self.open_profile_dialog
        )

        self.load_athletes()

    def load_athletes(self):

        athletes = self.repository.list_all()
        self.table.load(athletes)

    def search_athletes(self):

        text = self.toolbar.search.text().strip()

        if text == "":
            self.load_athletes()
            return

        athletes = self.repository.search(text)
        self.table.load(athletes)

    def open_new_athlete_dialog(self):

        dialog = NewAthleteDialog()

        if dialog.exec():
            self.search_athletes()

    def open_profile_dialog(self):

        athlete_id = self.table.selected_athlete_id()

        if athlete_id is None:
            return

        athlete = self.repository.get_by_id(athlete_id)

        if athlete is None:
            return

        dialog = AthleteProfileDialog(athlete)

        if dialog.exec():
            self.search_athletes()

    def delete_selected_athlete(self):

        athlete_id = self.table.selected_athlete_id()

        if athlete_id is None:

            QMessageBox.information(
                self,
                "Excluir atleta",
                "Selecione um atleta.",
            )

            return

        athlete = self.repository.get_by_id(athlete_id)

        if athlete is None:
            return

        resposta = QMessageBox.question(
            self,
            "Excluir atleta",
            f'Deseja excluir "{athlete.name}"?',
            QMessageBox.Yes | QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

        self.repository.delete(athlete.id)

        self.search_athletes()

        QMessageBox.information(
            self,
            "Sucesso",
            "Atleta excluído com sucesso.",
        )