from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from repositories.athlete_repository import AthleteRepository
from repositories.evaluation_repository import EvaluationRepository

from ui.athletes.dialogs.new_athlete_dialog import NewAthleteDialog
from ui.athletes.dialogs.new_evaluation_dialog import NewEvaluationDialog

from ui.athletes.widgets.athlete_general_tab import AthleteGeneralTab
from ui.athletes.widgets.athlete_header import AthleteHeader
from ui.athletes.widgets.evaluation_table import EvaluationTable
from ui.athletes.widgets.latest_evaluation_card import (
    LatestEvaluationCard,
)


class AthleteProfileDialog(QDialog):

    def __init__(self, athlete):
        super().__init__()

        self.repository = AthleteRepository()
        self.evaluation_repository = EvaluationRepository()

        self.athlete = athlete

        self.setWindowTitle("Perfil do Atleta")
        self.resize(750, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.header = AthleteHeader()
        layout.addWidget(self.header)

        self.tabs = QTabWidget()

        self.general_tab = AthleteGeneralTab()

        # =====================================================
        # Avaliações
        # =====================================================

        self.evaluations_tab = QWidget()

        evaluations_layout = QVBoxLayout(
            self.evaluations_tab
        )

        evaluations_layout.setSpacing(15)

        top = QHBoxLayout()

        self.btn_new_evaluation = QPushButton(
            "+ Nova Avaliação"
        )

        self.btn_delete_evaluation = QPushButton(
            "Excluir Avaliação"
        )

        top.addStretch()

        top.addWidget(self.btn_new_evaluation)
        top.addWidget(self.btn_delete_evaluation)

        evaluations_layout.addLayout(top)

        self.latest_evaluation = LatestEvaluationCard()
        evaluations_layout.addWidget(
            self.latest_evaluation
        )

        self.evaluation_table = EvaluationTable()
        evaluations_layout.addWidget(
            self.evaluation_table
        )

        # =====================================================

        self.tabs.addTab(
            self.general_tab,
            "Geral",
        )

        self.tabs.addTab(
            self.evaluations_tab,
            "Avaliações",
        )

        self.tabs.addTab(
            QWidget(),
            "Treinos",
        )

        self.tabs.addTab(
            QWidget(),
            "Histórico",
        )

        self.tabs.addTab(
            QWidget(),
            "Competições",
        )

        self.tabs.addTab(
            QWidget(),
            "Arquivos",
        )

        layout.addWidget(self.tabs)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.btn_edit = QPushButton("Editar")
        self.btn_close = QPushButton("Fechar")

        buttons.addWidget(self.btn_edit)
        buttons.addWidget(self.btn_close)

        layout.addLayout(buttons)

        self.btn_close.clicked.connect(
            self.reject
        )

        self.btn_edit.clicked.connect(
            self.edit_athlete
        )

        self.btn_new_evaluation.clicked.connect(
            self.new_evaluation
        )

        self.btn_delete_evaluation.clicked.connect(
            self.delete_evaluation
        )

        self.evaluation_table.doubleClicked.connect(
            self.edit_evaluation
        )

        self.load_data()

    def load_data(self):

        self.header.set_athlete(self.athlete)
        self.general_tab.set_athlete(
            self.athlete
        )

        evaluations = (
            self.evaluation_repository
            .list_by_athlete(
                self.athlete.id
            )
        )

        self.evaluation_table.load(
            evaluations
        )

        if evaluations:

            self.latest_evaluation.set_evaluation(
                evaluations[0]
            )

        else:

            self.latest_evaluation.clear()
            
    def edit_athlete(self):

        dialog = NewAthleteDialog(
            self.athlete
        )

        if dialog.exec():

            self.athlete = self.repository.get_by_id(
                self.athlete.id
            )

            self.load_data()

    def new_evaluation(self):

        dialog = NewEvaluationDialog(
            self.athlete
        )

        if dialog.exec():
            self.load_data()

    def edit_evaluation(self):

        evaluation = (
            self.evaluation_table.selected_evaluation()
        )

        if evaluation is None:

            QMessageBox.information(
                self,
                "Editar avaliação",
                "Selecione uma avaliação.",
            )

            return

        dialog = NewEvaluationDialog(
            self.athlete,
            evaluation,
        )

        if dialog.exec():
            self.load_data()

    def delete_evaluation(self):

        evaluation = (
            self.evaluation_table.selected_evaluation()
        )

        if evaluation is None:

            QMessageBox.information(
                self,
                "Excluir avaliação",
                "Selecione uma avaliação.",
            )

            return

        resposta = QMessageBox.question(
            self,
            "Excluir avaliação",
            "Deseja realmente excluir esta avaliação?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

        self.evaluation_repository.delete(
            evaluation.id
        )

        self.load_data()

        QMessageBox.information(
            self,
            "Sucesso",
            "Avaliação excluída com sucesso.",
        )

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Escape:
            self.reject()
            return

        super().keyPressEvent(event)        